CREATE TABLE `User` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(45) DEFAULT NULL,
  `about` text,
  `name` varchar(45) DEFAULT NULL,
  `email` varchar(45) NOT NULL,
  `isAnonymous` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_unique` (`email`),
  KEY `name_email` (`name`,`email`),
  KEY `email_name` (`email`,`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `Forum` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `short_name` varchar(45) NOT NULL,
  `user` varchar(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `short_name_unique` (`short_name`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `user` (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `Thread` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `forum` varchar(45) NOT NULL,
  `title` varchar(45) NOT NULL,
  `isClosed` tinyint(1) NOT NULL DEFAULT '0',
  `user` varchar(45) NOT NULL,
  `date` datetime NOT NULL,
  `message` text NOT NULL,
  `slug` varchar(45) NOT NULL,
  `isDeleted` tinyint(1) NOT NULL DEFAULT '0',
  `dislikes` int(11) NOT NULL DEFAULT '0',
  `likes` int(11) NOT NULL DEFAULT '0',
  `points` int(11) NOT NULL DEFAULT '0',
  `posts` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `forum_date` (`forum`,`date`),
  KEY `user_date` (`user`,`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `Post` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `thread` int(11) NOT NULL,
  `message` text NOT NULL,
  `user` varchar(45) NOT NULL,
  `forum` varchar(45) NOT NULL,
  `parent` int(11) DEFAULT NULL,
  `isApproved` tinyint(1) NOT NULL DEFAULT '0',
  `isHighlighted` tinyint(1) NOT NULL DEFAULT '0',
  `isEdited` tinyint(1) NOT NULL DEFAULT '0',
  `isSpam` tinyint(1) NOT NULL DEFAULT '0',
  `isDeleted` tinyint(1) NOT NULL DEFAULT '0',
  `dislikes` int(11) NOT NULL DEFAULT '0',
  `likes` int(11) NOT NULL DEFAULT '0',
  `points` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `forum_date_id` (`forum`,`date`,`id`),
  KEY `thread_date_id` (`thread`,`date`,`id`),
  KEY `user_date_id` (`user`,`date`,`id`),
  KEY `forum_user_id` (`forum`,`user`,`id`),
  KEY `thread_user_id` (`thread`,`user`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `PostHierarchy` (
  `post` int(11) NOT NULL,
  `parent` int(11) NOT NULL DEFAULT '0',
  `address` varchar(100) NOT NULL,
  PRIMARY KEY (`parent`,`address`,`post`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `Follower` (
  `name` varchar(45) NOT NULL,
  `followee` varchar(45) NOT NULL,
  PRIMARY KEY (`name`,`followee`),
  UNIQUE KEY `uk` (`name`,`followee`),
  KEY `followee` (`followee`,`name`),
  KEY `follower` (`name`,`followee`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `Subscription` (
  `name` varchar(45) NOT NULL,
  `thread` int(11) NOT NULL,
  PRIMARY KEY (`name`,`thread`),
  UNIQUE KEY `uk` (`name`,`thread`),
  KEY `subscription` (`name`,`thread`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
