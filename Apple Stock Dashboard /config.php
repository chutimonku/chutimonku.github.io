<?php
    $host = 'localhost';
    $username = 'root';
    $password = '';
    $database = 'apple_stock_data_2025';
    $conn = new mysqli($host, $username, $password, $database);

    if ($conn->connect_error) {
        die("Connection failed: " .$conn->connect_error);
    }
?>