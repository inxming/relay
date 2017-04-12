/*
SQLyog Ultimate v12.09 (64 bit)
MySQL - 5.7.17 : Database - replay
*********************************************************************
*/


/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`relay` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `relay`;

/*Table structure for table `inlog` */

DROP TABLE IF EXISTS `inlog`;

CREATE TABLE `inlog` (
      `id` bigint(20) NOT NULL AUTO_INCREMENT,
      `server_ip` varchar(20) NOT NULL,
      `ldap_user` varchar(30) NOT NULL,
      `os_user` varchar(20) NOT NULL,
      `cur_time` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
      `datas` text,
      `client_ip` varchar(20) DEFAULT NULL,
      PRIMARY KEY (`id`)

) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

