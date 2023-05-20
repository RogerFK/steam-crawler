/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

CREATE DATABASE IF NOT EXISTS `steam_tfg_jgg` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;
USE `steam_tfg_jgg`;

CREATE TABLE IF NOT EXISTS `candidate_appids` (
  `appid` int(10) unsigned NOT NULL,
  `count` int(10) unsigned NOT NULL DEFAULT 1,
  PRIMARY KEY (`appid`),
  KEY `count_candidates` (`count`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='The candidates to be explored, ordered by their count';

CREATE TABLE IF NOT EXISTS `categories` (
  `category_id` tinyint(3) unsigned NOT NULL,
  `category_description` varchar(64) NOT NULL,
  PRIMARY KEY (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Steam provides ID for categories, thus we don''t need a secondary key on the name';

CREATE TABLE IF NOT EXISTS `developers` (
  `developer_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `developer_name` varchar(256) NOT NULL,
  PRIMARY KEY (`developer_id`),
  UNIQUE KEY `unique_developer_name` (`developer_name`),
  KEY `developer_name` (`developer_name`)
) ENGINE=InnoDB AUTO_INCREMENT=19582 DEFAULT CHARSET=utf8mb4 COMMENT='ID -> developer name, name -> ID (the API returns a name, we need this as an indexed key too)\r\n256 because there''s a developer called "Ubisoft Quebec, in collaboration with Ubisoft Annecy, Bucharest, Kiev, Montreal, Montpellier, Shanghai, Singapore, Sofia, Toronto studios"';

CREATE TABLE IF NOT EXISTS `game_categories` (
  `appid` int(10) unsigned NOT NULL,
  `category_id` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`appid`,`category_id`),
  KEY `category_id_gc_fk` (`category_id`),
  KEY `appid_gc_fk` (`appid`),
  CONSTRAINT `appid_gc_fk` FOREIGN KEY (`appid`) REFERENCES `game_details` (`appid`) ON DELETE CASCADE,
  CONSTRAINT `category_id_gc_fk` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Relates games to categories';

CREATE TABLE IF NOT EXISTS `game_details` (
  `appid` int(10) unsigned NOT NULL,
  `name` varchar(128) NOT NULL,
  `required_age` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `is_free` bit(1) NOT NULL DEFAULT b'0',
  `controller_support` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `has_demo` bit(1) NOT NULL DEFAULT b'0',
  `price_usd` int(10) unsigned NOT NULL DEFAULT 0,
  `mac_os` bit(1) NOT NULL DEFAULT b'0',
  `positive_reviews` int(10) unsigned NOT NULL DEFAULT 0,
  `negative_reviews` int(10) unsigned NOT NULL DEFAULT 0,
  `total_reviews` int(10) unsigned NOT NULL DEFAULT 0,
  `has_achievements` bit(1) NOT NULL DEFAULT b'0',
  `release_date` varchar(64) DEFAULT NULL COMMENT 'Developers can set it to Coming Soon or various formats',
  `coming_soon` bit(1) NOT NULL DEFAULT b'0',
  `date_retrieved` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`appid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Game details provided via the Steam API';

CREATE TABLE IF NOT EXISTS `game_developers` (
  `appid` int(10) unsigned NOT NULL,
  `developer_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`appid`,`developer_id`),
  KEY `developer_id_gd_fk` (`developer_id`),
  KEY `appid_gd_fk` (`appid`),
  CONSTRAINT `appid_gd_fk` FOREIGN KEY (`appid`) REFERENCES `game_details` (`appid`) ON DELETE CASCADE,
  CONSTRAINT `developer_id_gd_fk` FOREIGN KEY (`developer_id`) REFERENCES `developers` (`developer_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Relation between game_details appid and developers';

CREATE TABLE IF NOT EXISTS `game_genres` (
  `appid` int(10) unsigned NOT NULL,
  `genre_id` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`appid`,`genre_id`),
  KEY `genre_id_gg_fk` (`genre_id`),
  KEY `appid_gg_fk` (`appid`),
  CONSTRAINT `appid_gg_fk` FOREIGN KEY (`appid`) REFERENCES `game_details` (`appid`) ON DELETE CASCADE,
  CONSTRAINT `genre_id_gg_fk` FOREIGN KEY (`genre_id`) REFERENCES `genres` (`genre_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Relation between game and genres, Steam provides IDs for genres';

CREATE TABLE IF NOT EXISTS `game_publishers` (
  `appid` int(10) unsigned NOT NULL,
  `publisher_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`appid`,`publisher_id`),
  KEY `publisher_id_gp_fk` (`publisher_id`),
  KEY `appid_gp_fk` (`appid`),
  CONSTRAINT `appid_gp_fk` FOREIGN KEY (`appid`) REFERENCES `game_details` (`appid`) ON DELETE CASCADE,
  CONSTRAINT `publisher_id_gp_fk` FOREIGN KEY (`publisher_id`) REFERENCES `publishers` (`publisher_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Relation between game appid and the respective publisher';

CREATE TABLE IF NOT EXISTS `game_tags` (
  `appid` int(10) unsigned NOT NULL,
  `tagid` int(10) unsigned NOT NULL,
  `weight` float NOT NULL DEFAULT -1,
  PRIMARY KEY (`appid`,`tagid`) USING BTREE,
  KEY `tagid_game_tags` (`tagid`) USING BTREE,
  KEY `appid_game_tags` (`appid`),
  CONSTRAINT `appid_game_tags_fk` FOREIGN KEY (`appid`) REFERENCES `game_details` (`appid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `tagid_game_tags_fk` FOREIGN KEY (`tagid`) REFERENCES `tags` (`tagid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tags scrapped from the store, with a relation of appid -> tagid\r\n';

CREATE TABLE IF NOT EXISTS `genres` (
  `genre_id` smallint(5) unsigned NOT NULL,
  `genre_description` varchar(64) NOT NULL,
  PRIMARY KEY (`genre_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Valve provides IDs for genres, it''s just ID -> genre';

CREATE TABLE IF NOT EXISTS `player_data` (
  `steamid` bigint(20) unsigned NOT NULL,
  `personaname` varchar(64) DEFAULT NULL,
  `commentpermission` tinyint(3) unsigned DEFAULT NULL,
  `primaryclanid` bigint(20) unsigned DEFAULT NULL,
  `timecreated` datetime DEFAULT NULL,
  `loccountrycode` varchar(2) CHARACTER SET utf8mb3 DEFAULT NULL,
  `locstatecode` varchar(4) CHARACTER SET utf8mb3 DEFAULT NULL,
  `loccityid` mediumint(8) unsigned DEFAULT NULL,
  `num_games_owned` smallint(5) unsigned NOT NULL DEFAULT 0,
  `num_reviews` smallint(5) unsigned NOT NULL DEFAULT 0,
  `visibility` tinyint(3) unsigned DEFAULT NULL COMMENT '1 if private, 2 if public but gamelist is private, 3 if public and game list is public but no times, 4 if everything is public',
  `date_retrieved` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`steamid`),
  KEY `primaryclanid` (`primaryclanid`),
  KEY `visibility` (`visibility`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Data retrieved from Steam. Only users with public profiles were crawled.';

CREATE TABLE IF NOT EXISTS `player_games` (
  `steamid` bigint(21) unsigned NOT NULL,
  `appid` int(10) unsigned NOT NULL,
  `playtime_forever` int(10) unsigned NOT NULL,
  `playtime_windows` int(10) unsigned DEFAULT NULL,
  `playtime_mac` int(10) unsigned DEFAULT NULL,
  `playtime_linux` int(10) unsigned DEFAULT NULL,
  `rtime_last_played` timestamp NOT NULL,
  PRIMARY KEY (`steamid`,`appid`),
  KEY `steamid_pdata` (`steamid`),
  KEY `appid_pdata` (`appid`),
  CONSTRAINT `appid_pd_fk` FOREIGN KEY (`appid`) REFERENCES `game_details` (`appid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `steamid_pd_fk` FOREIGN KEY (`steamid`) REFERENCES `player_data` (`steamid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Stores generic data for games, useful when there''s no review but we still want to store playtime';

CREATE TABLE IF NOT EXISTS `player_game_reviews` (
  `recommendationid` int(11) NOT NULL,
  `steamid` bigint(20) unsigned NOT NULL,
  `appid` int(10) unsigned NOT NULL,
  `voted_up` bit(1) NOT NULL COMMENT 'Recommended/Not Recommended',
  `timestamp_created` timestamp NOT NULL,
  `timestamp_updated` timestamp NOT NULL,
  `playtime_at_review` int(10) unsigned NOT NULL,
  `received_for_free` bit(1) NOT NULL,
  `steam_purchase` bit(1) NOT NULL,
  `written_during_early_access` bit(1) NOT NULL,
  PRIMARY KEY (`recommendationid`),
  UNIQUE KEY `steamid_appid_unique_reviews` (`steamid`,`appid`),
  KEY `steamid_reviews` (`steamid`),
  KEY `appid_reviews` (`appid`),
  KEY `steamid_appid_key_reviews` (`steamid`,`appid`),
  CONSTRAINT `appid_review` FOREIGN KEY (`appid`) REFERENCES `game_details` (`appid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `steamid_review` FOREIGN KEY (`steamid`) REFERENCES `player_data` (`steamid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Steam provides a recommendation ID, the text of the review, etc. but most aren''t relevant or are out of scope for this final degree project.\r\nVotes and comments would only be relevant if we were analyzing steam reviews like "perfect game" = 1000 votes and "not so good" = 50 votes, 2 clown awards would yield "everyone agrees this game is a 10/10", but a more sophisticated AI would be needed';

CREATE TABLE IF NOT EXISTS `processed_appids` (
  `appid` int(10) unsigned NOT NULL,
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`appid`),
  CONSTRAINT `processed_appid` FOREIGN KEY (`appid`) REFERENCES `game_details` (`appid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `publishers` (
  `publisher_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `publisher_name` varchar(128) NOT NULL,
  PRIMARY KEY (`publisher_id`) USING BTREE,
  UNIQUE KEY `unique_publisher_name` (`publisher_name`),
  KEY `publisher_name` (`publisher_name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=14334 DEFAULT CHARSET=utf8mb4 COMMENT='ID -> developer name, name -> ID (the API returns a name, we need this as an indexed key too)';

CREATE TABLE IF NOT EXISTS `tags` (
  `tagid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(60) DEFAULT NULL,
  PRIMARY KEY (`tagid`),
  KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1254553 DEFAULT CHARSET=utf8mb4;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
