-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: pisid_maze
-- ------------------------------------------------------
-- Server version	5.5.5-10.4.32-MariaDB

CREATE DATABASE IF NOT EXISTS pisid_maze;
USE pisid_maze;

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alertas`
--

DROP TABLE IF EXISTS `alertas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alertas` (
  `idAlerta` int(11) NOT NULL AUTO_INCREMENT,
  `idSimulacao` int(11) DEFAULT NULL,
  `Som` tinyint(1) DEFAULT 0,
  `Temperatura` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`idAlerta`),
  KEY `idSimulacao` (`idSimulacao`),
  CONSTRAINT `alertas_ibfk_1` FOREIGN KEY (`idSimulacao`) REFERENCES `simulacao` (`idSimulacao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alertas`
--

LOCK TABLES `alertas` WRITE;
/*!40000 ALTER TABLE `alertas` DISABLE KEYS */;
/*!40000 ALTER TABLE `alertas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `corredor`
--

DROP TABLE IF EXISTS `corredor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `corredor` (
  `idSimulacao` int(11) NOT NULL,
  `RoomA` int(11) NOT NULL,
  `RoomB` int(11) NOT NULL,
  `EstadoAberto` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`idSimulacao`,`RoomA`,`RoomB`),
  KEY `idSimulacao` (`idSimulacao`,`RoomB`),
  CONSTRAINT `corredor_ibfk_1` FOREIGN KEY (`idSimulacao`, `RoomA`) REFERENCES `ocupacaolabirinto` (`idSimulacao`, `idSala`),
  CONSTRAINT `corredor_ibfk_2` FOREIGN KEY (`idSimulacao`, `RoomB`) REFERENCES `ocupacaolabirinto` (`idSimulacao`, `idSala`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `corredor`
--

LOCK TABLES `corredor` WRITE;
/*!40000 ALTER TABLE `corredor` DISABLE KEYS */;
/*!40000 ALTER TABLE `corredor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `equipa`
--

DROP TABLE IF EXISTS `equipa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `equipa` (
  `idEquipa` int(11) NOT NULL,
  `nomeEquipa` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`idEquipa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `equipa`
--

LOCK TABLES `equipa` WRITE;
/*!40000 ALTER TABLE `equipa` DISABLE KEYS */;
/*!40000 ALTER TABLE `equipa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `marsamis`
--

DROP TABLE IF EXISTS `marsamis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `marsamis` (
  `idSimulacao` int(11) NOT NULL,
  `idMarsami` int(11) NOT NULL,
  `Tipo` varchar(20) DEFAULT NULL,
  `Cansado` tinyint(1) DEFAULT 0,
  `idSalaAtual` int(11) DEFAULT NULL,
  PRIMARY KEY (`idSimulacao`,`idMarsami`),
  KEY `idSimulacao` (`idSimulacao`,`idSalaAtual`),
  CONSTRAINT `marsamis_ibfk_1` FOREIGN KEY (`idSimulacao`, `idSalaAtual`) REFERENCES `ocupacaolabirinto` (`idSimulacao`, `idSala`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `marsamis`
--

LOCK TABLES `marsamis` WRITE;
/*!40000 ALTER TABLE `marsamis` DISABLE KEYS */;
/*!40000 ALTER TABLE `marsamis` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mensagens`
--

DROP TABLE IF EXISTS `mensagens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mensagens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `idSimulacao` int(11) DEFAULT NULL,
  `Hora` timestamp NULL DEFAULT NULL,
  `Sala` int(11) DEFAULT NULL,
  `Sensor` varchar(10) DEFAULT NULL,
  `Leitura` decimal(6,2) DEFAULT NULL,
  `TipoAlerta` varchar(50) DEFAULT NULL,
  `Msg` varchar(100) DEFAULT NULL,
  `HoraEscrita` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idSimulacao` (`idSimulacao`),
  CONSTRAINT `mensagens_ibfk_1` FOREIGN KEY (`idSimulacao`) REFERENCES `simulacao` (`idSimulacao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mensagens`
--

LOCK TABLES `mensagens` WRITE;
/*!40000 ALTER TABLE `mensagens` DISABLE KEYS */;
/*!40000 ALTER TABLE `mensagens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ocupacaolabirinto`
--

DROP TABLE IF EXISTS `ocupacaolabirinto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ocupacaolabirinto` (
  `idSimulacao` int(11) NOT NULL,
  `idSala` int(11) NOT NULL,
  `nrMarsamisOdd` int(11) DEFAULT 0,
  `nrMarsamisEven` int(11) DEFAULT 0,
  `tentativasPontuacao` int(11) DEFAULT 0,
  PRIMARY KEY (`idSimulacao`,`idSala`),
  CONSTRAINT `ocupacaolabirinto_ibfk_1` FOREIGN KEY (`idSimulacao`) REFERENCES `simulacao` (`idSimulacao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ocupacaolabirinto`
--

LOCK TABLES `ocupacaolabirinto` WRITE;
/*!40000 ALTER TABLE `ocupacaolabirinto` DISABLE KEYS */;
/*!40000 ALTER TABLE `ocupacaolabirinto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `salaequilibrada`
--

DROP TABLE IF EXISTS `salaequilibrada`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `salaequilibrada` (
  `idSimulacao` int(11) NOT NULL,
  `Sala` int(11) NOT NULL,
  PRIMARY KEY (`idSimulacao`,`Sala`),
  CONSTRAINT `salaequilibrada_ibfk_1` FOREIGN KEY (`idSimulacao`, `Sala`) REFERENCES `ocupacaolabirinto` (`idSimulacao`, `idSala`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `salaequilibrada`
--

LOCK TABLES `salaequilibrada` WRITE;
/*!40000 ALTER TABLE `salaequilibrada` DISABLE KEYS */;
/*!40000 ALTER TABLE `salaequilibrada` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `setupmaze`
--

DROP TABLE IF EXISTS `setupmaze`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `setupmaze` (
  `idSetup` int(11) NOT NULL AUTO_INCREMENT,
  `nrRooms` int(11) DEFAULT NULL,
  `nrMarsamis` int(11) DEFAULT NULL,
  `nrPlayers` int(11) DEFAULT NULL,
  `normalTemp` decimal(6,2) DEFAULT NULL,
  `tempVarHighTol` decimal(6,2) DEFAULT NULL,
  `tempVarLowTol` decimal(6,2) DEFAULT NULL,
  `normalSom` decimal(6,2) DEFAULT NULL,
  `somVarTol` decimal(6,2) DEFAULT NULL,
  PRIMARY KEY (`idSetup`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `setupmaze`
--

LOCK TABLES `setupmaze` WRITE;
/*!40000 ALTER TABLE `setupmaze` DISABLE KEYS */;
/*!40000 ALTER TABLE `setupmaze` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `simulacao`
--

DROP TABLE IF EXISTS `simulacao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `simulacao` (
  `idSimulacao` int(11) NOT NULL AUTO_INCREMENT,
  `Descricao` text DEFAULT NULL,
  `IDEquipa` int(11) DEFAULT NULL,
  `DataHoraInicio` timestamp NULL DEFAULT NULL,
  `IDSetup` int(11) DEFAULT NULL,
  `IsActive` tinyint(1) DEFAULT NULL,
  `CriadorEmail` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`idSimulacao`),
  KEY `IDEquipa` (`IDEquipa`),
  KEY `IDSetup` (`IDSetup`),
  CONSTRAINT `simulacao_ibfk_1` FOREIGN KEY (`IDEquipa`) REFERENCES `equipa` (`idEquipa`),
  CONSTRAINT `simulacao_ibfk_2` FOREIGN KEY (`IDSetup`) REFERENCES `setupmaze` (`idSetup`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `simulacao`
--

LOCK TABLES `simulacao` WRITE;
/*!40000 ALTER TABLE `simulacao` DISABLE KEYS */;
/*!40000 ALTER TABLE `simulacao` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `corredores_mapa`
--

DROP TABLE IF EXISTS `corredores_mapa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `corredores_mapa` (
  `idSimulacao` int(11) NOT NULL,
  `RoomA` int(11) NOT NULL,
  `RoomB` int(11) NOT NULL,
  PRIMARY KEY (`idSimulacao`,`RoomA`,`RoomB`),
  CONSTRAINT `fk_simulacao_corredores` FOREIGN KEY (`idSimulacao`) REFERENCES `simulacao` (`idSimulacao`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `corredores_mapa`
--

LOCK TABLES `corredores_mapa` WRITE;
/*!40000 ALTER TABLE `corredores_mapa` DISABLE KEYS */;
/*!40000 ALTER TABLE `corredores_mapa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `som`
--

DROP TABLE IF EXISTS `som`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `som` (
  `idSom` int(11) NOT NULL AUTO_INCREMENT,
  `idSimulacao` int(11) DEFAULT NULL,
  `Hora` timestamp NULL DEFAULT NULL,
  `Som` decimal(6,2) DEFAULT NULL,
  PRIMARY KEY (`idSom`),
  KEY `idSimulacao` (`idSimulacao`),
  CONSTRAINT `som_ibfk_1` FOREIGN KEY (`idSimulacao`) REFERENCES `simulacao` (`idSimulacao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `som`
--

LOCK TABLES `som` WRITE;
/*!40000 ALTER TABLE `som` DISABLE KEYS */;
/*!40000 ALTER TABLE `som` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `temperatura`
--

DROP TABLE IF EXISTS `temperatura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `temperatura` (
  `idTemp` int(11) NOT NULL AUTO_INCREMENT,
  `idSimulacao` int(11) DEFAULT NULL,
  `Hora` timestamp NULL DEFAULT NULL,
  `Temp` decimal(6,2) DEFAULT NULL,
  PRIMARY KEY (`idTemp`),
  KEY `idSimulacao` (`idSimulacao`),
  CONSTRAINT `temperatura_ibfk_1` FOREIGN KEY (`idSimulacao`) REFERENCES `simulacao` (`idSimulacao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `temperatura`
--

LOCK TABLES `temperatura` WRITE;
/*!40000 ALTER TABLE `temperatura` DISABLE KEYS */;
/*!40000 ALTER TABLE `temperatura` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `utilizador`
--

DROP TABLE IF EXISTS `utilizador`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `utilizador` (
  `idUtilizador` int(11) NOT NULL AUTO_INCREMENT,
  `Equipa` int(11) DEFAULT NULL,
  `Nome` varchar(100) DEFAULT NULL,
  `Tipo` varchar(3) DEFAULT NULL,
  `Telemovel` varchar(12) DEFAULT NULL,
  `Email` varchar(50) DEFAULT NULL,
  `DataNasc` date DEFAULT NULL,
  PRIMARY KEY (`idUtilizador`),
  KEY `Equipa` (`Equipa`),
  CONSTRAINT `utilizador_ibfk_1` FOREIGN KEY (`Equipa`) REFERENCES `equipa` (`idEquipa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `utilizador`
--

LOCK TABLES `utilizador` WRITE;
/*!40000 ALTER TABLE `utilizador` DISABLE KEYS */;
/*!40000 ALTER TABLE `utilizador` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

--
-- Table structure for table `historico_movimentos`
--

DROP TABLE IF EXISTS `historico_movimentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historico_movimentos` (
  `idMovimento` int(11) NOT NULL AUTO_INCREMENT,
  `idSimulacao` int(11) NOT NULL,
  `idMarsami` int(11) NOT NULL,
  `Hora` timestamp NULL DEFAULT NULL,
  `SalaOrigem` int(11) NOT NULL,
  `SalaDestino` int(11) NOT NULL,
  `Status` int(11) NOT NULL,
  PRIMARY KEY (`idMovimento`),
  KEY `fk_marsami_movimentos` (`idSimulacao`,`idMarsami`),
  CONSTRAINT `fk_marsami_movimentos` FOREIGN KEY (`idSimulacao`, `idMarsami`) REFERENCES `marsamis` (`idSimulacao`, `idMarsami`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historico_movimentos`
--

LOCK TABLES `historico_movimentos` WRITE;
/*!40000 ALTER TABLE `historico_movimentos` DISABLE KEYS */;
/*!40000 ALTER TABLE `historico_movimentos` ENABLE KEYS */;
UNLOCK TABLES;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-08 19:05:44
