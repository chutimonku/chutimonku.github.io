<?php
declare(strict_types=1);

//  Runtime & headers (ปิด error บนหน้า, ตั้ง cache, gzip)
ini_set('display_errors','0');
ini_set('display_startup_errors','0');
error_reporting(E_ALL);
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
if (function_exists('ini_get') && ini_get('zlib.output_compression') !== '1') { @ini_set('zlib.output_compression','1'); }
ob_start();
require_once __DIR__.'/config.php';
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=86400, s-maxage=86400, stale-while-revalidate=600');

// Helpers (fail() สำหรับตอบ error, normalizeDateParam(), eachDateISO())
function fail($msg){ ob_clean(); echo json_encode(['ok'=>false,'error'=>$msg], JSON_UNESCAPED_UNICODE); exit; }
function normalizeDateParam(?string $s): ?string {
  if (!$s) return null;
  $s = trim($s);
  $datePart = (strpos($s,' ')!==false) ? substr($s,0,strpos($s,' ')) : $s;
  if (preg_match('/^\d{4}-\d{2}-\d{2}$/',$datePart)) return $datePart;
  if (preg_match('/^\d{2}-\d{2}-\d{4}$/',$datePart)) { $dt=DateTime::createFromFormat('d-m-Y',$datePart); return $dt?$dt->format('Y-m-d'):null; }
  if (preg_match('/^\d{1,2}\/\d{1,2}\/\d{4}$/',$datePart)) { $dt=DateTime::createFromFormat('d/m/Y',$datePart); return $dt?$dt->format('Y-m-d'):null; }
  return null;
}
function eachDateISO(string $fromISO, string $toISO, string $order='ASC'): array {
  $a=new DateTimeImmutable($fromISO); $b=new DateTimeImmutable($toISO);
  if ($a>$b) { [$a,$b]=[$b,$a]; }
  $out=[]; for($d=$a;$d<=$b;$d=$d->modify('+1 day')){ $out[]=$d->format('Y-m-d'); }
  if (strtoupper($order)==='DESC') $out=array_reverse($out);
  return $out;
}

//  DB guard (เช็ค $conn และ charset)
if (!isset($conn) || !($conn instanceof mysqli)) fail('ไม่พบ $conn จาก config.php');
mysqli_set_charset($conn,'utf8mb4');

try {
  // Table & params (ชื่อ table, โหมด, ลำดับ, flags, ช่วงวัน)
  $TABLE = 'apple_stock';
  $chk = $conn->query("SHOW TABLES LIKE '".$conn->real_escape_string($TABLE)."'");
  if ($chk->num_rows===0) fail("ไม่พบตาราง '$TABLE'");

  $mode  = $_GET['mode']  ?? 'series';
  $order = (isset($_GET['order']) && strtolower($_GET['order'])==='desc') ? 'DESC' : 'ASC';
  $calendar = isset($_GET['calendar']) ? (int)$_GET['calendar'] : 0;
  $ffill    = isset($_GET['ffill'])    ? (int)$_GET['ffill']    : 0;

  $fromIso = normalizeDateParam($_GET['from'] ?? null);
  $toIso   = normalizeDateParam($_GET['to']   ?? null);
  if (isset($_GET['from']) && !$fromIso) fail("พารามิเตอร์ 'from' รูปแบบวันไม่รองรับ");
  if (isset($_GET['to'])   && !$toIso)   fail("พารามิเตอร์ 'to' รูปแบบวันไม่รองรับ");

  // Date normalize ใน SQL (CASE → YYYY-MM-DD) + คอลัมน์สำหรับ ORDER BY
  $D = "TRIM(`Date`)";
  $DT = "
    CASE
      WHEN $D REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'         THEN $D
      WHEN $D REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2} '         THEN LEFT($D,10)
      WHEN $D REGEXP '^[0-9]{2}-[0-9]{2}-[0-9]{4}($| )'     THEN DATE_FORMAT(STR_TO_DATE(LEFT($D,10),'%d-%m-%Y'),'%Y-%m-%d')
      WHEN $D REGEXP '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}($| )' THEN DATE_FORMAT(STR_TO_DATE(SUBSTRING_INDEX($D,' ',1),'%d/%m/%Y'),'%Y-%m-%d')
      ELSE NULL
    END
  ";
  $DT_ORDER = "STR_TO_DATE($DT, '%Y-%m-%d')";

  // โหมดหลัก: series (ดึง time-series ตามช่วง)
  if ($mode==='series') {
    $wheres = ["$DT_ORDER IS NOT NULL"];
    $params = []; $types='';
    if ($fromIso) { $wheres[] = "$DT_ORDER >= STR_TO_DATE(?, '%Y-%m-%d')"; $params[]=$fromIso; $types.='s'; }
    if ($toIso)   { $wheres[] = "$DT_ORDER <= STR_TO_DATE(?, '%Y-%m-%d')"; $params[]=$toIso;   $types.='s'; }
    $whereSql = 'WHERE '.implode(' AND ',$wheres);

    $sql = "
      SELECT
        $DT                 AS date,
        `Open`      + 0.0   AS open,
        `High`      + 0.0   AS high,
        `Low`       + 0.0   AS low,
        `Close`     + 0.0   AS close,
        `Adj Close` + 0.0   AS adj_close,
        `Volume`            AS volume
      FROM `$TABLE`
      $whereSql
      ORDER BY $DT_ORDER $order
    ";

    $stmt = $conn->prepare($sql);
    if ($params) $stmt->bind_param($types, ...$params);
    $stmt->execute();
    $res = $stmt->get_result();

    $data=[]; while($r=$res->fetch_assoc()){
      if ($r['date']===null) continue;
      $data[]=[
        'date'=>$r['date'],
        'open'=>(float)$r['open'],
        'high'=>(float)$r['high'],
        'low'=>(float)$r['low'],
        'close'=>(float)$r['close'],
        'adj_close'=>(float)$r['adj_close'],
        'volume'=>(int)$r['volume'],
        'is_trading'=>1
      ];
    }
    if (!count($data)) fail('ไม่พบข้อมูลหลังแปลงวันที่');
    $rows_trading = count($data);

    // Calendar expansion + forward-fill 
    if ($calendar===1) {
      $startISO = $fromIso ?: $data[0]['date'];
      $endISO   = $toIso   ?: $data[$rows_trading-1]['date'];
      $map=[]; foreach($data as $row) $map[$row['date']]=$row;
      $allDays = eachDateISO($startISO,$endISO,$order);
      $expanded=[]; $lastClose=null; $lastAdj=null;

      foreach($allDays as $d){
        if (isset($map[$d])){
          $row=$map[$d]; $lastClose=$row['close']; $lastAdj=$row['adj_close']; $expanded[]=$row;
        } else {
          $expanded[]=[
            'date'=>$d,'open'=>null,'high'=>null,'low'=>null,
            'close'=>($ffill?$lastClose:null),'adj_close'=>($ffill?$lastAdj:null),
            'volume'=>null,'is_trading'=>0
          ];
        }
      }
      $data=$expanded;
    }

    // Conditional GET (Last-Modified/304)
    $lastISO = ($order==='ASC') ? $data[count($data)-1]['date'] : $data[0]['date'];
    $lastTime = strtotime($lastISO.' 00:00:00 UTC');
    if ($lastTime!==false){
      $lastMod = gmdate('D, d M Y H:i:s',$lastTime).' GMT';
      header('Last-Modified: '.$lastMod);
      if (isset($_SERVER['HTTP_IF_MODIFIED_SINCE'])) {
        $ims=strtotime($_SERVER['HTTP_IF_MODIFIED_SINCE']);
        if ($ims!==false && $ims>=$lastTime){ http_response_code(304); ob_end_clean(); exit; }
      }
    }

    //  Output JSON
    ob_clean();
    echo json_encode([
      'ok'=>true,
      'mode'=>'series',
      'calendar'=>(bool)$calendar,
      'ffill'=>(bool)$ffill,
      'order'=>strtolower($order),
      'rows_total'=>count($data),
      'rows_trading'=>$rows_trading,
      'data'=>$data
    ], JSON_UNESCAPED_UNICODE);
    exit;
  }

  // Unsupported mode
  fail('unknown mode');

} catch (Throwable $e) {
  // Global error handler → JSON
  ob_clean();
  echo json_encode(['ok'=>false,'error'=>'DB/PHP error: '.$e->getMessage()], JSON_UNESCAPED_UNICODE);
}
exit;
