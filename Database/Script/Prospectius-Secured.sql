/*
 * Script optimisé pour la base de données du projet Prospectius
 * Auteur : josoavj
 * Version : 2.0 - Normalisation, sécurité et efficacité accrues
 */

CREATE DATABASE IF NOT EXISTS Prospectius CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE Prospectius;

--
-- Table pour la normalisation des rôles
--
CREATE TABLE Role (
  id_role INT AUTO_INCREMENT PRIMARY KEY,
  nom_role VARCHAR(50) NOT NULL UNIQUE,
  description TEXT NULL
);

--
-- Structure optimisée de la table 'Compte' (sans le salt)
--
CREATE TABLE Compte (
  id_compte INT AUTO_INCREMENT PRIMARY KEY,
  nom_compte VARCHAR(50) NOT NULL,
  prenom_compte VARCHAR(50) NOT NULL,
  nom_utilisateur VARCHAR(100) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL, -- Inclut le sel (ex: Bcrypt)
  statut_compte ENUM('actif', 'inactif', 'suspendu') NOT NULL DEFAULT 'actif',
  derniere_connexion DATETIME NULL,
  tentatives_connexion TINYINT DEFAULT 0,
  compte_verrouille_jusqu DATETIME NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_by INT NULL,
  updated_by INT NULL,

  CONSTRAINT CHK_password_length CHECK (CHAR_LENGTH(password_hash) >= 60), -- Longueur Bcrypt
  CONSTRAINT CHK_email_format CHECK (email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),
  CONSTRAINT FK_compte_created_by FOREIGN KEY (created_by) REFERENCES Compte(id_compte) ON DELETE SET NULL,
  CONSTRAINT FK_compte_updated_by FOREIGN KEY (updated_by) REFERENCES Compte(id_compte) ON DELETE SET NULL
);

--
-- Table de jointure pour les rôles des comptes
--
CREATE TABLE Compte_Role (
  id_compte_fk INT NOT NULL,
  id_role_fk INT NOT NULL,
  PRIMARY KEY (id_compte_fk, id_role_fk),
  CONSTRAINT FK_compte_role_compte FOREIGN KEY (id_compte_fk) REFERENCES Compte(id_compte) ON DELETE CASCADE,
  CONSTRAINT FK_compte_role_role FOREIGN KEY (id_role_fk) REFERENCES Role(id_role) ON DELETE CASCADE
);

--
-- Table pour normaliser les adresses
--
CREATE TABLE Adresse (
  id_adresse INT AUTO_INCREMENT PRIMARY KEY,
  ligne1 VARCHAR(255) NOT NULL,
  ligne2 VARCHAR(255) NULL,
  code_postal VARCHAR(10) NULL,
  ville VARCHAR(100) NULL,
  pays VARCHAR(50) DEFAULT 'Madagascar'
);

--
-- Structure optimisée de la table 'Prospect'
--
CREATE TABLE Prospect (
  id_prospect INT AUTO_INCREMENT PRIMARY KEY,
  date_creation DATE DEFAULT (CURRENT_DATE),
  nom_prospect VARCHAR(50) NOT NULL,
  prenom_prospect VARCHAR(50) NOT NULL,
  email_prospect VARCHAR(100) NOT NULL UNIQUE,
  telephone_prospect VARCHAR(20) NOT NULL,
  id_adresse_fk INT NOT NULL,
  resume_prospect TEXT DEFAULT NULL,
  statut_prospect ENUM('accepté', 'en attente', 'refusé', 'en_cours_traitement') DEFAULT 'en attente',
  priorite ENUM('basse', 'normale', 'haute', 'urgente') DEFAULT 'normale',
  source_prospect ENUM('web', 'telephone', 'email', 'referral', 'publicite', 'autre') NULL,
  valeur_estimee DECIMAL(15,2) NULL,
  date_suivi_prevue DATE NULL,
  notes_internes TEXT NULL,
  id_compte_fk INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  updated_by INT NULL,

  CONSTRAINT FK_prospect_adresse FOREIGN KEY (id_adresse_fk) REFERENCES Adresse(id_adresse) ON DELETE RESTRICT,
  CONSTRAINT CHK_telephone_format CHECK (telephone_prospect REGEXP '^[0-9+\\-\\s()]+$'),
  CONSTRAINT CHK_valeur_estimee CHECK (valeur_estimee >= 0),
  CONSTRAINT FK_compte FOREIGN KEY (id_compte_fk) REFERENCES Compte(id_compte) ON DELETE SET NULL,
  CONSTRAINT FK_prospect_updated_by FOREIGN KEY (updated_by) REFERENCES Compte(id_compte) ON DELETE SET NULL
);

--
-- Table Historique optimisée avec un lien vers la cause
--
CREATE TABLE Historique (
  id_historique INT AUTO_INCREMENT PRIMARY KEY,
  id_prospect_fk INT NOT NULL,
  ancien_statut ENUM('accepté', 'en attente', 'refusé', 'en_cours_traitement') NOT NULL,
  nouveau_statut ENUM('accepté', 'en attente', 'refusé', 'en_cours_traitement') NOT NULL,
  date_changement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  commentaire TEXT NULL,
  valeur_finale DECIMAL(15,2) NULL,
  id_compte_modificateur INT NULL,
  id_action_fk INT NULL, -- Lien vers Communication ou Tache

  CONSTRAINT FK_historique_prospect FOREIGN KEY (id_prospect_fk) REFERENCES Prospect(id_prospect) ON DELETE CASCADE,
  CONSTRAINT FK_historique_compte FOREIGN KEY (id_compte_modificateur) REFERENCES Compte(id_compte) ON DELETE SET NULL
);

-- =====================================================
-- TABLES SUPPLÉMENTAIRES POUR FONCTIONNALITÉS AVANCÉES
-- =====================================================

CREATE TABLE Communication (
  id_communication INT AUTO_INCREMENT PRIMARY KEY,
  id_prospect_fk INT NOT NULL,
  type_communication ENUM('email', 'telephone', 'reunion', 'courrier', 'autre') NOT NULL,
  sujet VARCHAR(255) NOT NULL,
  contenu TEXT NULL,
  date_communication DATETIME DEFAULT CURRENT_TIMESTAMP,
  statut ENUM('planifie', 'realise', 'annule') DEFAULT 'realise',
  id_compte_fk INT NOT NULL,

  CONSTRAINT FK_communication_prospect FOREIGN KEY (id_prospect_fk) REFERENCES Prospect(id_prospect) ON DELETE CASCADE,
  CONSTRAINT FK_communication_compte FOREIGN KEY (id_compte_fk) REFERENCES Compte(id_compte) ON DELETE RESTRICT
);

CREATE TABLE Tache (
  id_tache INT AUTO_INCREMENT PRIMARY KEY,
  id_prospect_fk INT NOT NULL,
  titre VARCHAR(255) NOT NULL,
  description TEXT NULL,
  date_echeance DATE NOT NULL,
  statut_tache ENUM('en_attente', 'en_cours', 'terminee', 'annulee') DEFAULT 'en_attente',
  priorite ENUM('basse', 'normale', 'haute', 'urgente') DEFAULT 'normale',
  id_compte_assigne INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT FK_tache_prospect FOREIGN KEY (id_prospect_fk) REFERENCES Prospect(id_prospect) ON DELETE CASCADE,
  CONSTRAINT FK_tache_compte FOREIGN KEY (id_compte_assigne) REFERENCES Compte(id_compte) ON DELETE RESTRICT
);

CREATE TABLE Journal_Audit (
  id_audit INT AUTO_INCREMENT PRIMARY KEY,
  table_concernee VARCHAR(50) NOT NULL,
  id_enregistrement INT NOT NULL,
  action ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
  anciennes_valeurs JSON NULL,
  nouvelles_valeurs JSON NULL,
  id_compte_utilisateur INT NULL,
  adresse_ip VARCHAR(45) NULL,
  date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT FK_audit_compte FOREIGN KEY (id_compte_utilisateur) REFERENCES Compte(id_compte) ON DELETE SET NULL
);

CREATE TABLE Session_Utilisateur (
  id_session VARCHAR(128) PRIMARY KEY,
  id_compte_fk INT NOT NULL,
  adresse_ip VARCHAR(45) NOT NULL,
  user_agent TEXT NULL,
  date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  date_expiration TIMESTAMP NOT NULL,
  actif BOOLEAN DEFAULT TRUE,

  CONSTRAINT FK_session_compte FOREIGN KEY (id_compte_fk) REFERENCES Compte(id_compte) ON DELETE CASCADE
);

-- =====================================================
-- INDEX POUR OPTIMISATION DES PERFORMANCES
-- =====================================================

CREATE INDEX idx_prospect_date_creation ON Prospect (date_creation);
CREATE INDEX idx_prospect_priorite ON Prospect (priorite);
CREATE INDEX idx_prospect_compte ON Prospect (id_compte_fk);
CREATE INDEX idx_prospect_statut_priorite ON Prospect (statut_prospect, priorite);
CREATE INDEX idx_compte_email ON Compte (email);
CREATE INDEX idx_compte_statut ON Compte (statut_compte);
CREATE INDEX idx_historique_prospect_date ON Historique (id_prospect_fk, date_changement);
CREATE INDEX idx_communication_prospect_date ON Communication (id_prospect_fk, date_communication);
CREATE INDEX idx_tache_assignee_echeance ON Tache (id_compte_assigne, date_echeance);
CREATE INDEX idx_tache_statut ON Tache (statut_tache);
CREATE INDEX idx_audit_table_date ON Journal_Audit (table_concernee, date_action);
CREATE INDEX idx_session_compte_actif ON Session_Utilisateur (id_compte_fk, actif);
CREATE INDEX idx_prospect_id_adresse ON Prospect (id_adresse_fk);

-- =====================================================
-- VUES POUR FACILITER LES REQUÊTES
-- =====================================================

CREATE OR REPLACE VIEW v_prospect_complet AS
SELECT
  p.id_prospect,
  p.nom_prospect,
  p.prenom_prospect,
  p.email_prospect,
  p.telephone_prospect,
  a.ligne1 AS adresse_prospect,
  a.code_postal,
  a.ville,
  a.pays,
  p.statut_prospect,
  p.priorite,
  p.valeur_estimee,
  p.date_creation,
  p.date_suivi_prevue,
  c.nom_compte AS gestionnaire_nom,
  c.prenom_compte AS gestionnaire_prenom,
  c.email AS gestionnaire_email,
  (SELECT COUNT(*) FROM Communication com WHERE com.id_prospect_fk = p.id_prospect) AS nb_communications,
  (SELECT COUNT(*) FROM Tache t WHERE t.id_prospect_fk = p.id_prospect AND t.statut_tache != 'terminee') AS taches_ouvertes
FROM Prospect p
LEFT JOIN Compte c ON p.id_compte_fk = c.id_compte
JOIN Adresse a ON p.id_adresse_fk = a.id_adresse;

-- La vue v_dashboard_utilisateur reste inchangée
CREATE OR REPLACE VIEW v_dashboard_utilisateur AS
SELECT
  c.id_compte,
  c.nom_compte,
  c.prenom_compte,
  COUNT(DISTINCT p.id_prospect) AS total_prospects,
  COUNT(DISTINCT CASE WHEN p.statut_prospect = 'en attente' THEN p.id_prospect END) AS prospects_en_attente,
  COUNT(DISTINCT CASE WHEN p.statut_prospect = 'accepté' THEN p.id_prospect END) AS prospects_acceptes,
  COUNT(DISTINCT CASE WHEN t.statut_tache = 'en_attente' THEN t.id_tache END) AS taches_en_attente,
  COUNT(DISTINCT CASE WHEN t.date_echeance < CURDATE() AND t.statut_tache != 'terminee' THEN t.id_tache END) AS taches_en_retard,
  SUM(CASE WHEN p.statut_prospect = 'accepté' THEN p.valeur_estimee ELSE 0 END) AS valeur_totale_acceptee
FROM Compte c
LEFT JOIN Prospect p ON c.id_compte = p.id_compte_fk
LEFT JOIN Tache t ON c.id_compte = t.id_compte_assigne
WHERE c.statut_compte = 'actif'
GROUP BY c.id_compte, c.nom_compte, c.prenom_compte;

-- =====================================================
-- TRIGGERS POUR AUTOMATISATION
-- =====================================================

DELIMITER //

--
-- Trigger pour journaliser les modifications des prospects
--
CREATE TRIGGER tr_prospect_audit_insert
AFTER INSERT ON Prospect
FOR EACH ROW
BEGIN
  INSERT INTO Journal_Audit (table_concernee, id_enregistrement, action, nouvelles_valeurs, id_compte_utilisateur)
  VALUES ('Prospect', NEW.id_prospect, 'INSERT',
    JSON_OBJECT(
      'nom_prospect', NEW.nom_prospect,
      'prenom_prospect', NEW.prenom_prospect,
      'email_prospect', NEW.email_prospect,
      'statut_prospect', NEW.statut_prospect,
      'id_compte_fk', NEW.id_compte_fk,
      'id_adresse_fk', NEW.id_adresse_fk
    ),
    NEW.id_compte_fk
  );
END//

CREATE TRIGGER tr_prospect_audit_update
AFTER UPDATE ON Prospect
FOR EACH ROW
BEGIN
  INSERT INTO Journal_Audit (table_concernee, id_enregistrement, action, anciennes_valeurs, nouvelles_valeurs, id_compte_utilisateur)
  VALUES ('Prospect', NEW.id_prospect, 'UPDATE',
    JSON_OBJECT(
      'statut_prospect', OLD.statut_prospect,
      'priorite', OLD.priorite,
      'valeur_estimee', OLD.valeur_estimee
    ),
    JSON_OBJECT(
      'statut_prospect', NEW.statut_prospect,
      'priorite', NEW.priorite,
      'valeur_estimee', NEW.valeur_estimee
    ),
    NEW.updated_by
  );

  -- Si le statut a changé, ajouter à l'historique
  IF OLD.statut_prospect != NEW.statut_prospect THEN
    INSERT INTO Historique (id_prospect_fk, ancien_statut, nouveau_statut, id_compte_modificateur, valeur_finale)
    VALUES (NEW.id_prospect, OLD.statut_prospect, NEW.statut_prospect, NEW.updated_by,
      CASE WHEN NEW.statut_prospect = 'accepté' THEN NEW.valeur_estimee ELSE NULL END
    );
  END IF;
END//

CREATE TRIGGER tr_compte_verrouillage
BEFORE UPDATE ON Compte
FOR EACH ROW
BEGIN
  IF NEW.tentatives_connexion >= 5 AND OLD.tentatives_connexion < 5 THEN
    SET NEW.compte_verrouille_jusqu = DATE_ADD(NOW(), INTERVAL 30 MINUTE);
    SET NEW.statut_compte = 'suspendu';
  END IF;

  IF NEW.tentatives_connexion = 0 THEN
    SET NEW.compte_verrouille_jusqu = NULL;
    IF OLD.statut_compte = 'suspendu' THEN
      SET NEW.statut_compte = 'actif';
    END IF;
  END IF;
END//


DELIMITER ;

-- =====================================================
-- PROCÉDURES STOCKÉES MISES À JOUR
-- =====================================================

DELIMITER //

--
-- Procédure pour créer un compte utilisateur avec validation complète
--
CREATE PROCEDURE sp_creer_compte(
  IN p_nom VARCHAR(50),
  IN p_prenom VARCHAR(50),
  IN p_nom_utilisateur VARCHAR(100),
  IN p_email VARCHAR(100),
  IN p_password_hash VARCHAR(255),
  IN p_id_role INT,
  IN p_created_by INT
)
BEGIN
  DECLARE v_count INT DEFAULT 0;
  DECLARE v_id_compte INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- Vérifier l'unicité de l'email et du nom d'utilisateur
  SELECT COUNT(*) INTO v_count FROM Compte WHERE email = p_email OR nom_utilisateur = p_nom_utilisateur;
  IF v_count > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'L\'email ou le nom d\'utilisateur est déjà utilisé';
  END IF;

  INSERT INTO Compte (nom_compte, prenom_compte, nom_utilisateur, email, password_hash, created_by)
  VALUES (p_nom, p_prenom, p_nom_utilisateur, p_email, p_password_hash, p_created_by);

  SET v_id_compte = LAST_INSERT_ID();

  -- Assigner le rôle au compte
  INSERT INTO Compte_Role (id_compte_fk, id_role_fk) VALUES (v_id_compte, p_id_role);

  COMMIT;

  SELECT 'Compte créé avec succès' AS message, v_id_compte AS id_compte;
END//

--
-- Procédure pour authentifier un utilisateur
--
CREATE PROCEDURE sp_authentifier_utilisateur(
  IN p_email VARCHAR(100),
  IN p_password_hash VARCHAR(255),
  IN p_adresse_ip VARCHAR(45)
)
BEGIN
  DECLARE v_id_compte INT;
  DECLARE v_password_hash_stored VARCHAR(255);
  DECLARE v_statut VARCHAR(20);
  DECLARE v_tentatives INT;
  DECLARE v_verrouille_jusqu DATETIME;

  SELECT id_compte, password_hash, statut_compte, tentatives_connexion, compte_verrouille_jusqu
  INTO v_id_compte, v_password_hash_stored, v_statut, v_tentatives, v_verrouille_jusqu
  FROM Compte
  WHERE email = p_email;

  IF v_id_compte IS NULL THEN
    SELECT 'Identifiants invalides' AS message, FALSE AS succes;
  ELSEIF v_verrouille_jusqu IS NOT NULL AND v_verrouille_jusqu > NOW() THEN
    SELECT 'Compte verrouillé temporairement' AS message, FALSE AS succes;
  ELSEIF v_statut != 'actif' THEN
    SELECT 'Compte inactif' AS message, FALSE AS succes;
  ELSE

    IF p_password_hash = v_password_hash_stored THEN
      UPDATE Compte
      SET derniere_connexion = NOW(), tentatives_connexion = 0
      WHERE id_compte = v_id_compte;

      SELECT 'Connexion réussie' AS message, TRUE AS succes, v_id_compte AS id_compte;
    ELSE
      UPDATE Compte
      SET tentatives_connexion = tentatives_connexion + 1
      WHERE id_compte = v_id_compte;

      SELECT 'Identifiants invalides' AS message, FALSE AS succes;
    END IF;
  END IF;
END//

CREATE PROCEDURE sp_statistiques_prospects(
  IN p_id_compte INT,
  IN p_date_debut DATE,
  IN p_date_fin DATE
)
BEGIN
  SELECT
    COUNT(*) as total_prospects,
    COUNT(CASE WHEN statut_prospect = 'en attente' THEN 1 END) as en_attente,
    COUNT(CASE WHEN statut_prospect = 'accepté' THEN 1 END) as acceptes,
    COUNT(CASE WHEN statut_prospect = 'refusé' THEN 1 END) as refuses,
    COUNT(CASE WHEN priorite = 'urgente' THEN 1 END) as urgents,
    AVG(valeur_estimee) as valeur_moyenne,
    SUM(CASE WHEN statut_prospect = 'accepté' THEN valeur_estimee ELSE 0 END) as valeur_totale_acceptee
  FROM Prospect
  WHERE (p_id_compte IS NULL OR id_compte_fk = p_id_compte)
    AND date_creation BETWEEN p_date_debut AND p_date_fin;
END//

CREATE PROCEDURE sp_nettoyage_donnees()
BEGIN
  DECLARE v_lignes_supprimees INT DEFAULT 0;
  DECLARE v_temp INT;

  START TRANSACTION;

  -- Supprimer les sessions expirées
  DELETE FROM Session_Utilisateur WHERE date_expiration < NOW();
  SET v_temp = ROW_COUNT();
  SET v_lignes_supprimees = v_lignes_supprimees + v_temp;

  -- Supprimer les anciens logs d'audit (> 1 an)
  DELETE FROM Journal_Audit WHERE date_action < DATE_SUB(NOW(), INTERVAL 1 YEAR);
  SET v_temp = ROW_COUNT();
  SET v_lignes_supprimees = v_lignes_supprimees + v_temp;

  -- Supprimer les tâches terminées anciennes (> 6 mois)
  DELETE FROM Tache
  WHERE statut_tache = 'terminee'
    AND updated_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
  SET v_temp = ROW_COUNT();
  SET v_lignes_supprimees = v_lignes_supprimees + v_temp;

  COMMIT;

  SELECT CONCAT(v_lignes_supprimees, ' enregistrements supprimés') AS message;
END//

CREATE PROCEDURE sp_assigner_prospects_automatiquement()
BEGIN
  DECLARE done INT DEFAULT FALSE;
  DECLARE v_id_prospect INT;
  DECLARE v_id_compte_min_charge INT;
  DECLARE v_prospects_assignes INT DEFAULT 0;

  DECLARE cur CURSOR FOR
    SELECT id_prospect
    FROM Prospect
    WHERE id_compte_fk IS NULL AND statut_prospect = 'en attente';
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

  OPEN cur;

  read_loop: LOOP
    FETCH cur INTO v_id_prospect;
    IF done THEN
      LEAVE read_loop;
    END IF;

    -- Trouver le compte utilisateur avec le moins de prospects en cours
    SELECT c.id_compte INTO v_id_compte_min_charge
    FROM Compte c
    LEFT JOIN Prospect p ON c.id_compte = p.id_compte_fk AND p.statut_prospect IN ('en attente', 'en_cours_traitement')
    LEFT JOIN Compte_Role cr ON c.id_compte = cr.id_compte_fk
    LEFT JOIN Role r ON cr.id_role_fk = r.id_role
    WHERE r.nom_role IN ('user', 'manager') AND c.statut_compte = 'actif'
    GROUP BY c.id_compte
    ORDER BY COUNT(p.id_prospect) ASC
    LIMIT 1;

    -- Assigner le prospect
    IF v_id_compte_min_charge IS NOT NULL THEN
      UPDATE Prospect
      SET id_compte_fk = v_id_compte_min_charge,
          statut_prospect = 'en_cours_traitement',
          updated_by = v_id_compte_min_charge
      WHERE id_prospect = v_id_prospect;

      SET v_prospects_assignes = v_prospects_assignes + 1;
    END IF;

  END LOOP;

  CLOSE cur;

  SELECT CONCAT('Assignment automatique terminé - ', v_prospects_assignes, ' prospects assignés') AS message;
END//

DELIMITER ;

-- =====================================================
-- DONNÉES INITIALES
-- =====================================================

INSERT INTO Role (nom_role, description) VALUES
('admin', 'Administrateur avec tous les droits'),
('manager', 'Manager de l\'équipe de vente'),
('user', 'Utilisateur standard pour la gestion des prospects');

-- =====================================================
-- ÉVÉNEMENTS PLANIFIÉS (optionnel)
-- =====================================================

-- L'événement planifié est conservé et est maintenant le seul responsable du nettoyage.
CREATE EVENT IF NOT EXISTS ev_nettoyage_quotidien
ON SCHEDULE EVERY 1 DAY
STARTS TIMESTAMP(CURRENT_DATE + INTERVAL 1 DAY, '02:00:00')
DO
  CALL sp_nettoyage_donnees();