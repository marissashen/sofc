USE mshen4_db;

DROP TABLE IF EXISTS appeal;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS supply;
DROP TABLE IF EXISTS honorarium;
DROP TABLE IF EXISTS formula;
DROP TABLE IF EXISTS food;
DROP TABLE IF EXISTS attendee;
DROP TABLE IF EXISTS cost;
DROP TABLE IF EXISTS event;
DROP TABLE IF EXISTS funding;
DROP TABLE IF EXISTS treasurer;
DROP TABLE IF EXISTS org;
DROP TABLE IF EXISTS user;

CREATE TABLE user
	(username VARCHAR(20) NOT NULL PRIMARY KEY,
	 uType ENUM('general', 'sofc', 'admin') NOT NULL,
 	 loginTimes INT NOT NULL DEFAULT 1) ENGINE=InnoDB;

CREATE TABLE org
	(name VARCHAR(100) NOT NULL PRIMARY KEY,
	 classification ENUM('academic', 'arts/performing arts', 'career', 'CG',
		 'class council', 'club sports', 'cultural', 'GP', 'house councils',
		 'media/publications', 'non athletic teams', 'political', 'religious',
		 'social justice', 'unconstituted', 'volunteer') NOT NULL,
	 sofc INT NOT NULL,
	 profit INT,
 	 canApply BOOLEAN NOT NULL DEFAULT TRUE) ENGINE=InnoDB;

CREATE TABLE treasurer
	(orgName VARCHAR(100) NOT NULL,
	 username VARCHAR(20) NOT NULL,
 	 FOREIGN KEY (orgName) REFERENCES org(name) ON DELETE CASCADE,
 	 FOREIGN KEY (username) REFERENCES user(username) ON DELETE CASCADE,
   PRIMARY KEY (orgName, username)) ENGINE=InnoDB;

CREATE TABLE funding
	(deadline DATETIME NOT NULL PRIMARY KEY,
	 appealsDeadline DATETIME,
	 fType ENUM('Fall', 'Fall Emergency', 'Uniquely Compelling', 'Spring',
		 'Spring Emergency', 'GP Review', 'Interim') NOT NULL,
	 budgetFood DECIMAL(9,2) NOT NULL,
	 budgetNonFood DECIMAL(9,2) NOT NULL) ENGINE=InnoDB;

CREATE TABLE event
	(id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	 treasurer VARCHAR(20) NOT NULL,
	 orgName VARCHAR(100) NOT NULL,
	 eventName VARCHAR(100) NOT NULL,
	 purpose VARCHAR(10000) NOT NULL,
	 eventDate DATE NOT NULL,
	 fundingDeadline DATETIME NOT NULL,
	 eType ENUM('Bonding', 'Eboard', 'Lecture', 'Mixer', 'Other', 'Party',
		 'Publication', 'Show', 'Tournament', 'Workshop') NOT NULL,
	 students INT NOT NULL,
	 foodReq DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 nonFoodReq DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 foodGrant DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 nonFoodGrant DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 fullyAllocatedFood BOOLEAN NOT NULL DEFAULT FALSE,
	 fullyAllocatedNonFood BOOLEAN NOT NULL DEFAULT FALSE,
	 foodAlloc DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 nonFoodAlloc DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 dollarStud DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 FOREIGN KEY (treasurer) REFERENCES user(username) ON DELETE RESTRICT,
	 FOREIGN KEY (orgName) REFERENCES org(name) ON DELETE RESTRICT,
	 FOREIGN KEY (fundingDeadline) REFERENCES funding(deadline) ON DELETE RESTRICT) ENGINE=InnoDB;

CREATE TABLE cost
	(eventID INT NOT NULL,
	 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	 treasurer VARCHAR(20) NOT NULL,
	 reviewer VARCHAR(20),
 	 reviewed BOOLEAN NOT NULL DEFAULT FALSE,
 	 totalReq DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 totalGrant DECIMAL(9,2) NOT NULL DEFAULT 0.00,
	 cType ENUM('Attendee', 'Food', 'Formula', 'Honorarium', 'Supply') NOT NULL,
	 FOREIGN KEY (eventID) REFERENCES event(id) ON DELETE CASCADE,
 	 FOREIGN KEY (treasurer) REFERENCES user(username) ON DELETE RESTRICT) ENGINE=InnoDB;

CREATE TABLE attendee
 (id INT NOT NULL PRIMARY KEY,
  pdf BLOB NOT NULL,
  FOREIGN KEY (id) REFERENCES cost(id) ON DELETE CASCADE) ENGINE=InnoDB;

CREATE TABLE food
	(id INT NOT NULL PRIMARY KEY,
 	 explanation VARCHAR(1000) NOT NULL,
	 FOREIGN KEY (id) REFERENCES cost(id) ON DELETE CASCADE) ENGINE=InnoDB;

CREATE TABLE formula
	(id INT NOT NULL PRIMARY KEY,
	 kind ENUM('car', 'crowd control', 'custodial', 'eboard', 'open meeting',
		 'programs', 'publicity', 'speaker meal') NOT NULL,
 	 input DECIMAL(9,2) NOT NULL,
	 output DECIMAL(9,2) NOT NULL,
	 pdf BLOB,
 	 FOREIGN KEY (id) REFERENCES cost(id) ON DELETE CASCADE) ENGINE=InnoDB;

CREATE TABLE honorarium
 (id INT NOT NULL PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	contract BLOB NOT NULL,
	FOREIGN KEY (id) REFERENCES cost(id) ON DELETE CASCADE) ENGINE=InnoDB;

CREATE TABLE supply
 	(id INT NOT NULL PRIMARY KEY,
 	 pdf1 BLOB NOT NULL,
 	 pdf2 BLOB,
 	 pdf3 BLOB,
 	 FOREIGN KEY (id) REFERENCES cost(id) ON DELETE CASCADE) ENGINE=InnoDB;

CREATE TABLE comment
	(id INT NOT NULL PRIMARY KEY,
	 commentor VARCHAR(20) NOT NULL,
	 note VARCHAR(1000) NOT NULL,
 	 FOREIGN KEY (id) REFERENCES cost(id) ON DELETE CASCADE,
 	 FOREIGN KEY (commentor) REFERENCES user(username) ON DELETE RESTRICT) ENGINE=InnoDB;

CREATE TABLE appeal
	(id INT NOT NULL PRIMARY KEY,
	 requestor VARCHAR(20),
	 treasurer VARCHAR(20),
	 reviewed BOOLEAN NOT NULL DEFAULT FALSE,
	 passer VARCHAR(20),
	 passed BOOLEAN NOT NULL DEFAULT FALSE,
	 explanation VARCHAR(10000) NOT NULL DEFAULT "RESPONSE NEEDED",
	 pdf BLOB,
	 FOREIGN KEY (id) REFERENCES cost(id) ON DELETE CASCADE) ENGINE=InnoDB;
