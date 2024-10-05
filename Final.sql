Create database prospectius;

use prospectius;

CREATE TABLE Compte (
  idCompte int(11) NOT NULL AUTO_INCREMENT,
  nomCompte varchar(50) NOT NULL,
  prenomCompte varchar(50) NOT NULL,
  n_utilisateur varchar(50) NOT NULL,
  mail varchar(100) NOT NULL,
  mdp varchar(8) NOT NULL,
  PRIMARY KEY (idCompte),
  UNIQUE KEY mail (mail)
);

CREATE TABLE Prospect (
  idProspect int(11) NOT NULL AUTO_INCREMENT,
  dateP date DEFAULT NULL,
  nomP varchar(50) NOT NULL,
  prenomP varchar(50) NOT NULL,
  mailP varchar(100) NOT NULL,
  numberP varchar(15) NOT NULL,
  adresseP varchar(255) NOT NULL,
  resumeP text DEFAULT NULL,
  conclusionP varchar(60) 
  DEFAULT 'En attente',
  PRIMARY KEY (idProspect),
  UNIQUE KEY mailP (mailP)
);

