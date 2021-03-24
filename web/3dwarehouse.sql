CREATE TABLE Person (
    username VARCHAR(32),
    password VARCHAR(64),
    email VARCHAR(32),
    PRIMARY KEY (username)
);

CREATE TABLE Photo (
    pID INT AUTO_INCREMENT,
    filePath VARCHAR(255), -- you may replace this by a BLOB attribute to store the actual photo
    username VARCHAR(32),
    PRIMARY KEY (pID),
    FOREIGN KEY (username) REFERENCES Person (username)
);