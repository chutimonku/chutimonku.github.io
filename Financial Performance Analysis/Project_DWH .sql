-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Mar 09, 2026 at 05:58 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `Project_DWH`
--

-- --------------------------------------------------------

--
-- Table structure for table `dim_company`
--

CREATE TABLE `dim_company` (
  `company_id` int(11) NOT NULL,
  `company_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_company`
--

INSERT INTO `dim_company` (`company_id`, `company_name`) VALUES
(1, 'McDonald\'s'),
(2, 'Starbucks');

-- --------------------------------------------------------

--
-- Table structure for table `dim_year`
--

CREATE TABLE `dim_year` (
  `year_id` int(11) NOT NULL,
  `year` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_year`
--

INSERT INTO `dim_year` (`year_id`, `year`) VALUES
(1, 2002),
(2, 2003),
(3, 2004),
(4, 2005),
(5, 2006),
(6, 2007),
(7, 2008),
(8, 2009),
(9, 2010),
(10, 2011),
(11, 2012),
(12, 2013),
(13, 2014),
(14, 2015),
(15, 2016),
(16, 2017),
(17, 2018),
(18, 2019),
(19, 2020),
(20, 2021),
(21, 2022),
(22, 2023),
(23, 2024),
(24, 2025);

-- --------------------------------------------------------

--
-- Table structure for table `fact_financial_kpi`
--

CREATE TABLE `fact_financial_kpi` (
  `company_id` int(11) NOT NULL,
  `year_id` int(11) NOT NULL,
  `revenue_b` decimal(10,2) DEFAULT NULL,
  `net_income_b` decimal(10,2) DEFAULT NULL,
  `total_assets_b` decimal(10,2) DEFAULT NULL,
  `total_debt_b` decimal(10,2) DEFAULT NULL,
  `total_liabilities_b` decimal(10,2) DEFAULT NULL,
  `cash_on_hand_b` decimal(10,2) DEFAULT NULL,
  `eps_usd` decimal(10,2) DEFAULT NULL,
  `operating_margin_pct` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_financial_kpi`
--

INSERT INTO `fact_financial_kpi` (`company_id`, `year_id`, `revenue_b`, `net_income_b`, `total_assets_b`, `total_debt_b`, `total_liabilities_b`, `cash_on_hand_b`, `eps_usd`, `operating_margin_pct`) VALUES
(1, 1, 15.40, 1.66, 23.97, 9.97, 13.68, 0.33, 0.70, 10.79),
(1, 2, 17.14, 2.34, 25.52, 9.73, 13.54, 0.49, 1.16, 13.69),
(1, 3, 19.06, 3.20, 27.83, 9.21, 13.63, 1.37, 1.82, 16.80),
(1, 4, 20.46, 3.70, 29.98, 10.14, 14.84, 4.26, 2.06, 18.09),
(1, 5, 20.81, 3.88, 29.02, 8.43, 13.56, 2.13, 2.88, 19.30),
(1, 6, 22.78, 3.57, 29.39, 9.30, 14.11, 1.98, 2.01, 15.68),
(1, 7, 23.52, 6.15, 28.46, 10.21, 15.07, 2.06, 3.84, 26.18),
(1, 8, 22.74, 6.48, 30.22, 10.57, 16.19, 1.79, 4.17, 28.52),
(1, 9, 24.07, 7.00, 31.97, 11.50, 17.34, 2.38, 4.66, 29.08),
(1, 10, 27.00, 8.01, 32.98, 12.50, 18.59, 2.33, 5.34, 29.67),
(1, 11, 27.56, 8.07, 35.38, 13.63, 20.09, 2.33, 5.42, 29.31),
(1, 12, 28.10, 8.20, 36.62, 14.12, 20.61, 2.79, 5.60, 29.19),
(1, 13, 27.44, 7.37, 34.28, 14.98, 21.42, 2.07, 4.87, 26.86),
(1, 14, 25.41, 6.55, 37.93, 24.12, 30.85, 7.68, 4.88, 25.80),
(1, 15, 24.62, 6.86, 31.02, 25.95, 33.22, 1.22, 5.53, 27.89),
(1, 16, 22.82, 8.57, 33.80, 29.53, 37.07, 2.46, 6.46, 37.57),
(1, 17, 21.02, 7.81, 32.81, 31.07, 39.06, 0.86, 7.65, 37.17),
(1, 18, 21.28, 8.01, 47.51, 46.87, 55.72, 0.89, 7.98, 38.04),
(1, 19, 19.20, 6.14, 52.62, 48.51, 60.45, 3.44, 6.35, 31.97),
(1, 20, 23.22, 9.12, 53.60, 48.64, 58.20, 4.70, 10.11, 39.31),
(1, 21, 23.18, 7.82, 50.43, 48.03, 56.43, 2.58, 8.42, 33.76),
(2, 10, 11.70, 1.40, 12.87, 5.79, 8.50, 1.76, 1.60, 16.00),
(2, 11, 13.28, 1.59, 14.61, 6.57, 9.40, 1.99, 1.80, 16.00),
(2, 12, 14.87, 1.78, 16.36, 7.36, 10.60, 2.23, 2.05, 16.00),
(2, 13, 16.45, 1.97, 18.09, 8.14, 11.70, 2.47, 2.30, 16.00),
(2, 14, 19.16, 2.30, 21.08, 9.49, 13.60, 2.87, 2.70, 16.00),
(2, 15, 21.32, 2.56, 23.45, 10.55, 15.20, 3.20, 3.00, 16.00),
(2, 16, 22.39, 2.69, 24.63, 11.08, 16.00, 3.36, 3.10, 16.00),
(2, 17, 24.72, 2.96, 27.19, 12.24, 17.80, 3.71, 3.40, 16.00),
(2, 18, 26.51, 3.18, 29.16, 13.12, 19.00, 3.98, 3.60, 16.00),
(2, 19, 23.52, 1.18, 25.87, 11.64, 18.20, 3.53, 1.20, 7.00),
(2, 20, 29.06, 3.49, 31.97, 14.38, 21.50, 4.36, 3.90, 16.00),
(2, 21, 32.25, 3.87, 35.48, 15.97, 23.60, 4.84, 4.20, 16.00);

-- --------------------------------------------------------

--
-- Table structure for table `fact_revenue`
--

CREATE TABLE `fact_revenue` (
  `company_id` int(11) NOT NULL,
  `year_id` int(11) NOT NULL,
  `revenue_b` decimal(10,2) DEFAULT NULL,
  `growth_rate` decimal(10,2) DEFAULT NULL,
  `q1` decimal(10,2) DEFAULT NULL,
  `q2` decimal(10,2) DEFAULT NULL,
  `q3` decimal(10,2) DEFAULT NULL,
  `q4` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_revenue`
--

INSERT INTO `fact_revenue` (`company_id`, `year_id`, `revenue_b`, `growth_rate`, `q1`, `q2`, `q3`, `q4`) VALUES
(1, 1, 15.40, 4.00, NULL, NULL, NULL, 3.00),
(1, 2, 17.10, 11.00, 3.80, 4.30, 4.50, 4.60),
(1, 3, 18.60, 8.00, 4.40, 4.70, 4.90, 4.50),
(1, 4, 19.10, 3.00, 4.80, 5.10, 5.30, 3.90),
(1, 5, 20.90, 9.00, 4.90, 5.40, 5.50, 5.10),
(1, 6, 22.80, 9.00, 5.30, 5.80, 5.90, 5.80),
(1, 7, 23.50, 3.00, 5.60, 6.10, 6.30, 5.60),
(1, 8, 22.70, -3.00, 5.10, 5.60, 6.00, 6.00),
(1, 9, 24.10, 6.00, 5.60, 5.90, 6.30, 6.20),
(1, 10, 27.00, 12.00, 6.10, 6.90, 7.20, 6.80),
(1, 11, 27.60, 2.00, 6.50, 6.90, 7.20, 7.00),
(1, 12, 28.10, 2.00, 6.60, 7.10, 7.30, 7.10),
(1, 13, 27.40, -2.00, 6.70, 7.20, 7.00, 6.60),
(1, 14, 25.40, -7.00, 6.00, 6.50, 6.60, 6.30),
(1, 15, 24.60, -3.00, 5.90, 6.30, 6.40, 6.00),
(1, 16, 22.80, -7.00, 5.70, 6.00, 5.80, 5.30),
(1, 17, 21.30, -7.00, 5.10, 5.40, 5.40, 5.40),
(1, 18, 21.40, 1.00, 5.00, 5.30, 5.60, 5.40),
(1, 19, 19.20, -10.00, 4.70, 3.80, 5.40, 5.30),
(1, 20, 23.20, 21.00, 5.10, 5.90, 6.20, 6.00),
(1, 21, 23.20, 0.00, 5.70, 5.70, 5.90, 5.90),
(2, 10, 11.70, NULL, 2.79, 2.93, 3.03, 3.44),
(2, 11, 13.28, 13.50, 3.20, 3.30, 3.34, 3.79),
(2, 12, 14.87, 11.97, 3.55, 3.74, 3.79, 4.24),
(2, 13, 16.45, 10.63, 3.87, 4.15, 4.18, 4.80),
(2, 14, 19.16, 16.47, 4.56, 4.88, 4.92, 5.37),
(2, 15, 21.32, 11.27, 4.99, 5.24, 5.71, 5.73),
(2, 16, 22.39, 5.02, 5.29, 5.66, 5.70, 6.07),
(2, 17, 24.72, 10.41, 6.03, 6.31, 6.30, 6.63),
(2, 18, 26.51, 7.24, 6.31, 6.82, 6.75, 7.10),
(2, 19, 23.52, -11.28, 6.00, 4.22, 6.20, 6.75),
(2, 20, 29.06, 23.55, 6.67, 7.50, 8.15, 8.05),
(2, 21, 32.25, 10.98, 7.64, 8.15, 8.41, 8.71),
(2, 22, 35.98, 11.57, 8.72, 9.17, 9.37, 9.43),
(2, 23, 36.18, 0.56, 8.56, 9.11, 9.07, 9.40),
(2, 24, 37.18, 2.76, 8.76, 9.46, 9.57, 9.92);

-- --------------------------------------------------------

--
-- Table structure for table `stg_mcd_financial`
--

CREATE TABLE `stg_mcd_financial` (
  `year` int(11) DEFAULT NULL,
  `market_cap_b` decimal(10,2) DEFAULT NULL,
  `revenue_b` decimal(10,2) DEFAULT NULL,
  `net_income_b` decimal(10,2) DEFAULT NULL,
  `pe_ratio` decimal(10,2) DEFAULT NULL,
  `ps_ratio` decimal(10,2) DEFAULT NULL,
  `pb_ratio` decimal(10,2) DEFAULT NULL,
  `operating_margin_pct` decimal(10,2) DEFAULT NULL,
  `eps_usd` decimal(10,2) DEFAULT NULL,
  `shares_outstanding_b` decimal(10,2) DEFAULT NULL,
  `cash_on_hand_b` decimal(10,2) DEFAULT NULL,
  `dividend_yield_pct` decimal(10,2) DEFAULT NULL,
  `dividend_stock_split_adj` decimal(10,2) DEFAULT NULL,
  `net_assets_b` decimal(10,2) DEFAULT NULL,
  `total_assets_b` decimal(10,2) DEFAULT NULL,
  `total_debt_b` decimal(10,2) DEFAULT NULL,
  `total_liabilities_b` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stg_mcd_financial`
--

INSERT INTO `stg_mcd_financial` (`year`, `market_cap_b`, `revenue_b`, `net_income_b`, `pe_ratio`, `ps_ratio`, `pb_ratio`, `operating_margin_pct`, `eps_usd`, `shares_outstanding_b`, `cash_on_hand_b`, `dividend_yield_pct`, `dividend_stock_split_adj`, `net_assets_b`, `total_assets_b`, `total_debt_b`, `total_liabilities_b`) VALUES
(2002, 20.39, 15.40, 1.66, 23.00, 1.32, 1.98, 10.79, 0.70, 1.27, 0.33, 1.46, 0.24, 10.28, 23.97, 9.97, 13.68),
(2003, 31.33, 17.14, 2.34, 21.40, 1.83, 2.62, 13.69, 1.16, 1.27, 0.49, 1.61, 0.40, 11.98, 25.52, 9.73, 13.54),
(2004, 40.71, 19.06, 3.20, 17.60, 2.14, 2.87, 16.80, 1.82, 1.25, 1.37, 1.72, 0.55, 14.20, 27.83, 9.21, 13.63),
(2005, 42.59, 20.46, 3.70, 16.40, 2.08, 2.81, 18.09, 2.06, 1.25, 4.26, 1.99, 0.67, 15.14, 29.98, 10.14, 14.84),
(2006, 53.36, 20.81, 3.88, 15.40, 2.56, 3.45, 19.30, 2.88, 1.23, 2.13, 2.26, 1.00, 15.45, 29.02, 8.43, 13.56),
(2007, 67.84, 22.78, 3.57, 29.30, 2.98, 4.44, 15.68, 2.01, 1.18, 1.98, 2.55, 1.50, 15.27, 29.39, 9.30, 14.11),
(2008, 69.31, 23.52, 6.15, 16.20, 2.95, 5.18, 26.18, 3.84, 1.11, 2.06, 2.61, 1.62, 13.38, 28.46, 10.21, 15.07),
(2009, 67.22, 22.74, 6.48, 15.00, 2.96, 4.79, 28.52, 4.17, 1.10, 1.79, 3.28, 2.05, 14.03, 30.22, 10.57, 16.19),
(2010, 80.87, 24.07, 7.00, 16.50, 3.36, 5.53, 29.08, 4.66, 1.05, 2.38, 2.94, 2.26, 14.63, 31.97, 11.50, 17.34),
(2011, 102.65, 27.00, 8.01, 18.80, 3.80, 7.13, 29.67, 5.34, 1.02, 2.33, 2.52, 2.53, 14.39, 32.98, 12.50, 18.59),
(2012, 88.44, 27.56, 8.07, 16.30, 3.21, 5.78, 29.31, 5.42, 1.00, 2.33, 3.25, 2.87, 15.29, 35.38, 13.63, 20.09),
(2013, 96.09, 28.10, 8.20, 17.30, 3.42, 6.00, 29.19, 5.60, 0.99, 2.79, 3.22, 3.12, 16.00, 36.62, 14.12, 20.61),
(2014, 90.22, 27.44, 7.37, 19.20, 3.29, 7.02, 26.86, 4.87, 0.96, 2.07, 3.50, 3.28, 12.85, 34.28, 14.98, 21.42),
(2015, 107.12, 25.41, 6.55, 24.20, 4.22, 15.10, 25.80, 4.88, 0.90, 7.68, 2.91, 3.44, 7.08, 37.93, 24.12, 30.85),
(2016, 101.08, 24.62, 6.86, 22.00, 4.11, -45.90, 27.89, 5.53, 0.81, 1.22, 2.97, 3.61, -2.21, 31.02, 25.95, 33.22),
(2017, 137.21, 22.82, 8.57, 26.70, 6.01, -42.00, 37.57, 6.46, 0.79, 2.46, 2.23, 3.83, -3.27, 33.80, 29.53, 37.07),
(2018, 136.21, 21.02, 7.81, 23.20, 6.48, -21.80, 37.17, 7.65, 0.76, 0.86, 2.36, 4.19, -6.26, 32.81, 31.07, 39.06),
(2019, 147.47, 21.28, 8.01, 24.80, 6.93, -18.00, 38.04, 7.98, 0.74, 0.89, 2.39, 4.73, -8.22, 47.51, 46.87, 55.72),
(2020, 159.88, 19.20, 6.14, 33.80, 8.32, -20.40, 31.97, 6.35, 0.74, 3.44, 2.35, 5.04, -7.83, 52.62, 48.51, 60.45),
(2021, 200.31, 23.22, 9.12, 26.50, 8.63, -43.50, 39.31, 10.11, 0.74, 4.70, 1.96, 5.25, -4.61, 53.60, 48.64, 58.20),
(2022, 193.01, 23.18, 7.82, 31.30, 8.33, -32.20, 33.76, 8.42, 0.73, 2.58, 2.15, 5.66, -6.01, 50.43, 48.03, 56.43);

-- --------------------------------------------------------

--
-- Table structure for table `stg_mcd_revenue`
--

CREATE TABLE `stg_mcd_revenue` (
  `year` int(11) DEFAULT NULL,
  `revenue_b` decimal(10,2) DEFAULT NULL,
  `growth_rate` decimal(10,2) DEFAULT NULL,
  `q1` decimal(10,2) DEFAULT NULL,
  `q2` decimal(10,2) DEFAULT NULL,
  `q3` decimal(10,2) DEFAULT NULL,
  `q4` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stg_mcd_revenue`
--

INSERT INTO `stg_mcd_revenue` (`year`, `revenue_b`, `growth_rate`, `q1`, `q2`, `q3`, `q4`) VALUES
(2002, 15.40, 4.00, NULL, NULL, NULL, 3.00),
(2003, 17.10, 11.00, 3.80, 4.30, 4.50, 4.60),
(2004, 18.60, 8.00, 4.40, 4.70, 4.90, 4.50),
(2005, 19.10, 3.00, 4.80, 5.10, 5.30, 3.90),
(2006, 20.90, 9.00, 4.90, 5.40, 5.50, 5.10),
(2007, 22.80, 9.00, 5.30, 5.80, 5.90, 5.80),
(2008, 23.50, 3.00, 5.60, 6.10, 6.30, 5.60),
(2009, 22.70, -3.00, 5.10, 5.60, 6.00, 6.00),
(2010, 24.10, 6.00, 5.60, 5.90, 6.30, 6.20),
(2011, 27.00, 12.00, 6.10, 6.90, 7.20, 6.80),
(2012, 27.60, 2.00, 6.50, 6.90, 7.20, 7.00),
(2013, 28.10, 2.00, 6.60, 7.10, 7.30, 7.10),
(2014, 27.40, -2.00, 6.70, 7.20, 7.00, 6.60),
(2015, 25.40, -7.00, 6.00, 6.50, 6.60, 6.30),
(2016, 24.60, -3.00, 5.90, 6.30, 6.40, 6.00),
(2017, 22.80, -7.00, 5.70, 6.00, 5.80, 5.30),
(2018, 21.30, -7.00, 5.10, 5.40, 5.40, 5.40),
(2019, 21.40, 1.00, 5.00, 5.30, 5.60, 5.40),
(2020, 19.20, -10.00, 4.70, 3.80, 5.40, 5.30),
(2021, 23.20, 21.00, 5.10, 5.90, 6.20, 6.00),
(2022, 23.20, 0.00, 5.70, 5.70, 5.90, 5.90);

-- --------------------------------------------------------

--
-- Table structure for table `stg_sbux_financial`
--

CREATE TABLE `stg_sbux_financial` (
  `year` int(11) DEFAULT NULL,
  `revenue_b` decimal(10,2) DEFAULT NULL,
  `net_income_b` decimal(10,2) DEFAULT NULL,
  `operating_income_b` decimal(10,2) DEFAULT NULL,
  `total_assets_b` decimal(10,2) DEFAULT NULL,
  `total_debt_b` decimal(10,2) DEFAULT NULL,
  `total_liabilities_b` decimal(10,2) DEFAULT NULL,
  `cash_on_hand_b` decimal(10,2) DEFAULT NULL,
  `eps_usd` decimal(10,2) DEFAULT NULL,
  `operating_margin_pct` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stg_sbux_financial`
--

INSERT INTO `stg_sbux_financial` (`year`, `revenue_b`, `net_income_b`, `operating_income_b`, `total_assets_b`, `total_debt_b`, `total_liabilities_b`, `cash_on_hand_b`, `eps_usd`, `operating_margin_pct`) VALUES
(2011, 11.70, 1.40, 1.87, 12.87, 5.79, 8.50, 1.76, 1.60, 16.00),
(2012, 13.28, 1.59, 2.12, 14.61, 6.57, 9.40, 1.99, 1.80, 16.00),
(2013, 14.87, 1.78, 2.38, 16.36, 7.36, 10.60, 2.23, 2.05, 16.00),
(2014, 16.45, 1.97, 2.63, 18.09, 8.14, 11.70, 2.47, 2.30, 16.00),
(2015, 19.16, 2.30, 3.07, 21.08, 9.49, 13.60, 2.87, 2.70, 16.00),
(2016, 21.32, 2.56, 3.41, 23.45, 10.55, 15.20, 3.20, 3.00, 16.00),
(2017, 22.39, 2.69, 3.58, 24.63, 11.08, 16.00, 3.36, 3.10, 16.00),
(2018, 24.72, 2.96, 3.96, 27.19, 12.24, 17.80, 3.71, 3.40, 16.00),
(2019, 26.51, 3.18, 4.24, 29.16, 13.12, 19.00, 3.98, 3.60, 16.00),
(2020, 23.52, 1.18, 1.65, 25.87, 11.64, 18.20, 3.53, 1.20, 7.00),
(2021, 29.06, 3.49, 4.65, 31.97, 14.38, 21.50, 4.36, 3.90, 16.00),
(2022, 32.25, 3.87, 5.16, 35.48, 15.97, 23.60, 4.84, 4.20, 16.00);

-- --------------------------------------------------------

--
-- Table structure for table `stg_sbux_revenue`
--

CREATE TABLE `stg_sbux_revenue` (
  `year` int(11) DEFAULT NULL,
  `revenue_b` decimal(10,2) DEFAULT NULL,
  `growth_rate` decimal(10,2) DEFAULT NULL,
  `q1` decimal(10,2) DEFAULT NULL,
  `q2` decimal(10,2) DEFAULT NULL,
  `q3` decimal(10,2) DEFAULT NULL,
  `q4` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stg_sbux_revenue`
--

INSERT INTO `stg_sbux_revenue` (`year`, `revenue_b`, `growth_rate`, `q1`, `q2`, `q3`, `q4`) VALUES
(2011, 11.70, NULL, 2.79, 2.93, 3.03, 3.44),
(2012, 13.28, 13.50, 3.20, 3.30, 3.34, 3.79),
(2013, 14.87, 11.97, 3.55, 3.74, 3.79, 4.24),
(2014, 16.45, 10.63, 3.87, 4.15, 4.18, 4.80),
(2015, 19.16, 16.47, 4.56, 4.88, 4.92, 5.37),
(2016, 21.32, 11.27, 4.99, 5.24, 5.71, 5.73),
(2017, 22.39, 5.02, 5.29, 5.66, 5.70, 6.07),
(2018, 24.72, 10.41, 6.03, 6.31, 6.30, 6.63),
(2019, 26.51, 7.24, 6.31, 6.82, 6.75, 7.10),
(2020, 23.52, -11.28, 6.00, 4.22, 6.20, 6.75),
(2021, 29.06, 23.55, 6.67, 7.50, 8.15, 8.05),
(2022, 32.25, 10.98, 7.64, 8.15, 8.41, 8.71),
(2023, 35.98, 11.57, 8.72, 9.17, 9.37, 9.43),
(2024, 36.18, 0.56, 8.56, 9.11, 9.07, 9.40),
(2025, 37.18, 2.76, 8.76, 9.46, 9.57, 9.92);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `dim_company`
--
ALTER TABLE `dim_company`
  ADD PRIMARY KEY (`company_id`);

--
-- Indexes for table `dim_year`
--
ALTER TABLE `dim_year`
  ADD PRIMARY KEY (`year_id`),
  ADD UNIQUE KEY `year` (`year`);

--
-- Indexes for table `fact_financial_kpi`
--
ALTER TABLE `fact_financial_kpi`
  ADD PRIMARY KEY (`company_id`,`year_id`),
  ADD KEY `year_id` (`year_id`);

--
-- Indexes for table `fact_revenue`
--
ALTER TABLE `fact_revenue`
  ADD PRIMARY KEY (`company_id`,`year_id`),
  ADD KEY `year_id` (`year_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `dim_company`
--
ALTER TABLE `dim_company`
  MODIFY `company_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `dim_year`
--
ALTER TABLE `dim_year`
  MODIFY `year_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `fact_financial_kpi`
--
ALTER TABLE `fact_financial_kpi`
  ADD CONSTRAINT `fact_financial_kpi_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `dim_company` (`company_id`),
  ADD CONSTRAINT `fact_financial_kpi_ibfk_2` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`);

--
-- Constraints for table `fact_revenue`
--
ALTER TABLE `fact_revenue`
  ADD CONSTRAINT `fact_revenue_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `dim_company` (`company_id`),
  ADD CONSTRAINT `fact_revenue_ibfk_2` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
