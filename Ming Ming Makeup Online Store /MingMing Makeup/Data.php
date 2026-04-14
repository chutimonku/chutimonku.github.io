<?php
// ข้อมูลสำหรับเชื่อมต่อฐานข้อมูล
$servername = "localhost";
$username = "root"; // เปลี่ยนเป็น username ของคุณ
$password = ""; // เปลี่ยนเป็น password ของคุณ
$dbname = "store"; // ชื่อฐานข้อมูล

// เชื่อมต่อฐานข้อมูล
$conn = new mysqli($servername, $username, $password, $dbname);

// ตรวจสอบการเชื่อมต่อ
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// รับคีย์เวิร์ดจาก URL
$query = isset($_GET['query']) ? $_GET['query'] : '';

// สร้างคำสั่ง SQL สำหรับค้นหาสินค้า
$sql = "SELECT * FROM products WHERE product_name LIKE '%$query%' OR description LIKE '%$query%'";
$result = $conn->query($sql);

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results</title>
</head>
<body>

<h1>Search Results for "<?php echo htmlspecialchars($query); ?>"</h1>

<?php
if ($result->num_rows > 0) {
    // แสดงรายการสินค้าที่พบ
    while($row = $result->fetch_assoc()) {
        echo "<div>";
        echo "<h2>" . $row["product_name"] . "</h2>";
        echo "<p>" . $row["description"] . "</p>";
        echo "<p>Price: " . $row["price"] . " ฿</p>";
        echo "</div><hr>";
    }
} else {
    echo "<p>No products found.</p>";
}

$conn->close();
?>

</body>
</html>
