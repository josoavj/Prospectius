/*
*    Script pour la base de données du projet Prospectius
*    Auteur : josoavj
*/
CREATE DATABASE IF NOT EXISTS Prospectius;

USE Prospectius;


/*
    Juste quatre tables:
    - Compte : pour les comptes utilisateurs
    - Administrateur : pour la gestion de compte admin
    - Prospect : pour les informations du prospect
    - Historique : pour l'historique des prospects devenus clients
*/

--
-- Structure de la table 'Compte'
--
CREATE TABLE Compte (
  id_compte INT AUTO_INCREMENT PRIMARY KEY,
  nom_compte VARCHAR(50) NOT NULL,
  prenom_compte VARCHAR(50) NOT NULL,
  nom_utilisateur VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  password VARCHAR(255) NOT NULL,
  role_compte ENUM('admin', 'user') NOT NULL DEFAULT 'user',
  CONSTRAINT UQ_email_compte UNIQUE (email),
  CONSTRAINT UQ_nom_prenom UNIQUE (nom_compte, prenom_compte),
  CONSTRAINT CHK_password CHECK (
    password NOT LIKE CONCAT('%', nom_compte, '%') AND
    password NOT LIKE CONCAT('%', prenom_compte, '%')
  )
);

--
-- Création d'une table pour gérer l'administrateur
--
CREATE TABLE Administrateur (
  id_admin INT PRIMARY KEY,
  CONSTRAINT FK_admin_compte FOREIGN KEY (id_admin) REFERENCES Compte(id_compte) ON DELETE CASCADE
);

--
-- Structure de la table 'Prospect'
--
CREATE TABLE Prospect (
  id_prospect INT AUTO_INCREMENT PRIMARY KEY,
  date_creation DATE DEFAULT (CURRENT_DATE),
  nom_prospect VARCHAR(50) NOT NULL,
  prenom_prospect VARCHAR(50) NOT NULL,
  email_prospect VARCHAR(100) NOT NULL,
  telephone_prospect VARCHAR(20) NOT NULL,
  adresse_prospect VARCHAR(255) NOT NULL,
  resume_prospect TEXT DEFAULT NULL,
  statut_prospect ENUM('accepté', 'en attente', 'refusé') DEFAULT 'en attente',
  id_compte_fk INT,
  CONSTRAINT UQ_email_prospect UNIQUE (email_prospect),
  CONSTRAINT FK_compte FOREIGN KEY (id_compte_fk) REFERENCES Compte(id_compte) ON DELETE SET NULL
);

--
-- Table pour gérer l'historique des prospects devenus clients
--
CREATE TABLE Historique (
  id_historique INT AUTO_INCREMENT PRIMARY KEY,
  id_prospect_fk INT NOT NULL,
  date_acceptation DATE DEFAULT (CURRENT_DATE),
  CONSTRAINT FK_historique_prospect FOREIGN KEY (id_prospect_fk) REFERENCES Prospect(id_prospect) ON DELETE CASCADE
);

--
-- Création d'un index pour optimiser les recherches sur le statut
--
CREATE INDEX idx_statut_prospect ON Prospect (statut_prospect);

/*
* Script modifié le 11 Août 2025
*/