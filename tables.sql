CREATE DATABASE IF NOT EXISTS dbapi;
GRANT ALL PRIVILEGES ON dbapi.* TO 'dbapi'@'localhost';

USE dbapi;

CREATE TABLE IF NOT EXISTS User (
    id int(11) NOT NULL AUTO_INCREMENT,
    username varchar(45),
    about text,
    name varchar(45),
    email varchar(45) NOT NULL,
    isAnonymous tinyint(1) DEFAULT '0',

    PRIMARY KEY (id),
    UNIQUE KEY email_unique (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS Forum (
    id int(11) NOT NULL AUTO_INCREMENT,
    name varchar(45) NOT NULL,
    short_name varchar(45) NOT NULL,
    user varchar(45) NOT NULL,

    PRIMARY KEY (id),
    UNIQUE KEY name (name),
    UNIQUE KEY short_name (short_name),
    CONSTRAINT forum_user FOREIGN KEY (user) REFERENCES User (email) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS Thread (
    id int(11) NOT NULL AUTO_INCREMENT,
    forum varchar(45) DEFAULT NULL,
    title varchar(45) DEFAULT NULL,
    isClosed tinyint(1) DEFAULT '0',
    user varchar(45) DEFAULT NULL,
    date datetime NOT NULL,
    message blob NOT NULL,
    slug varchar(45) DEFAULT NULL,
    isDeleted tinyint(1) DEFAULT '0',
    dislikes int(11) DEFAULT '0',
    likes int(11) DEFAULT '0',
    points int(11) DEFAULT '0',
    posts int(11) DEFAULT '0',

    PRIMARY KEY (id),
    UNIQUE KEY title (title),
    CONSTRAINT thread_user FOREIGN KEY (user) REFERENCES User (email) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT thread_forum FOREIGN KEY (forum) REFERENCES Forum (short_name) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS Post (
    id int(11) NOT NULL AUTO_INCREMENT,
    date datetime NOT NULL,
    thread int(11) NOT NULL,
    message blob NOT NULL,
    user varchar(45) DEFAULT NULL,
    forum varchar(45) DEFAULT NULL,
    parent int(11) DEFAULT NULL,
    isApproved tinyint(1) DEFAULT '0',
    isHighlighted tinyint(1) DEFAULT '0',
    isEdited tinyint(1) DEFAULT '0',
    isSpam tinyint(1) DEFAULT '0',
    isDeleted tinyint(1) DEFAULT '0',
    dislikes int(11) DEFAULT '0',
    likes int(11) DEFAULT '0',
    points int(11) DEFAULT '0',

    PRIMARY KEY (id),
    UNIQUE KEY user_date (user, date),
    CONSTRAINT post_user FOREIGN KEY (user) REFERENCES User (email) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT post_forum FOREIGN KEY (forum) REFERENCES Forum (short_name) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT post_thread FOREIGN KEY (thread) REFERENCES Thread (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS Follower (
    name varchar(45) NOT NULL,
    followee varchar(45) NOT NULL,

    PRIMARY KEY (name,followee),
    CONSTRAINT name_user FOREIGN KEY (name) REFERENCES User (email) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT followee_user FOREIGN KEY (followee) REFERENCES User (email) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS Followee (
    name varchar(45) NOT NULL,
    follower varchar(45) NOT NULL,

    PRIMARY KEY (name,follower),
    CONSTRAINT followee_name_user FOREIGN KEY (name) REFERENCES User (email) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT follower_user FOREIGN KEY (follower) REFERENCES User (email) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS Subscription (
    name varchar(45) NOT NULL,
    thread int(11) NOT NULL,
    
    PRIMARY KEY (name, thread),
    CONSTRAINT subscription_name_user FOREIGN KEY (name) REFERENCES User (email) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT subscription_thread FOREIGN KEY (thread) REFERENCES Thread (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS PostHierarchy (
    post int(11) NOT NULL DEFAULT '0',
    parent int(11) NOT NULL DEFAULT '0',
    address varchar(200) NOT NULL DEFAULT '',
    
    PRIMARY KEY (parent, address, post),
    UNIQUE KEY post (post, parent),
    CONSTRAINT post_foreign FOREIGN KEY (post) REFERENCES Post (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
