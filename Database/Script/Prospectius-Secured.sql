/*
*    Script optimisé pour la base de données du projet Prospectius
*    Auteur : josoavj (optimisé par Claude)
*    Version : 2.0 - Optimisée avec sécurité renforcée et fonctionnalités avancées
*/

CREATE DATABASE IF NOT EXISTS Prospectius CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE Prospectius;

-- =====================================================
-- TABLES PRINCIPALES
-- =====================================================

--
-- Structure optimisée de la table 'Compte'
--
CREATE TABLE Compte (
  id_compte INT AUTO_INCREMENT PRIMARY KEY,
  nom_compte VARCHAR(50) NOT NULL,
  prenom_compte VARCHAR(50) NOT NULL,
  nom_utilisateur VARCHAR(100) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL,
  password VARCHAR(255) NOT NULL,
  salt VARCHAR(32) NOT NULL, -- Pour le hachage sécurisé des mots de passe
  role_compte ENUM('admin', 'user', 'manager') NOT NULL DEFAULT 'user',
  statut_compte ENUM('actif', 'inactif', 'suspendu') NOT NULL DEFAULT 'actif',
  derniere_connexion DATETIME NULL,
  tentatives_connexion TINYINT DEFAULT 0,
  compte_verrouille_jusqu DATETIME NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_by INT NULL,
  updated_by INT NULL,

  CONSTRAINT UQ_email_compte UNIQUE (email),
  CONSTRAINT CHK_password_length CHECK (CHAR_LENGTH(password) >= 8),
  CONSTRAINT CHK_email_format CHECK (email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),
  CONSTRAINT FK_compte_created_by FOREIGN KEY (created_by) REFERENCES Compte(id_compte) ON DELETE SET NULL,
  CONSTRAINT FK_compte_updated_by FOREIGN KEY (updated_by) REFERENCES Compte(id_compte) ON DELETE SET NULL
);

--
-- Table Administrateur optimisée
--
CREATE TABLE Administrateur (
  id_admin INT PRIMARY KEY,
  niveau_acces ENUM('super_admin', 'admin', 'admin_lecture') NOT NULL DEFAULT 'admin',
  permissions JSON NULL, -- Permissions spécifiques sous format JSON
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT FK_admin_compte FOREIGN KEY (id_admin) REFERENCES Compte(id_compte) ON DELETE CASCADE
);

--
-- Structure optimisée de la table 'Prospect'
--
CREATE TABLE Prospect (
  id_prospect INT AUTO_INCREMENT PRIMARY KEY,
  date_creation DATE DEFAULT (CURRENT_DATE),
  nom_prospect VARCHAR(50) NOT NULL,
  prenom_prospect VARCHAR(50) NOT NULL,
  email_prospect VARCHAR(100) NOT NULL,
  telephone_prospect VARCHAR(20) NOT NULL,
  adresse_prospect VARCHAR(255) NOT NULL,
  code_postal VARCHAR(10) NULL,
  ville VARCHAR(100) NULL,
  pays VARCHAR(50) DEFAULT 'Madagascar',
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

  CONSTRAINT UQ_email_prospect UNIQUE (email_prospect),
  CONSTRAINT CHK_email_prospect_format CHECK (email_prospect REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),
  CONSTRAINT CHK_telephone_format CHECK (telephone_prospect REGEXP '^[0-9+\\-\\s()]+$'),
  CONSTRAINT CHK_valeur_estimee CHECK (valeur_estimee >= 0),
  CONSTRAINT FK_compte FOREIGN KEY (id_compte_fk) REFERENCES Compte(id_compte) ON DELETE SET NULL,
  CONSTRAINT FK_prospect_updated_by FOREIGN KEY (updated_by) REFERENCES Compte(id_compte) ON DELETE SET NULL
);

--
-- Table Historique optimisée avec plus de détails
--
CREATE TABLE Historique (
  id_historique INT AUTO_INCREMENT PRIMARY KEY,
  id_prospect_fk INT NOT NULL,
  ancien_statut ENUM('accepté', 'en attente', 'refusé', 'en_cours_traitement') NOT NULL,
  nouveau_statut ENUM('accepté', 'en attente', 'refusé', 'en_cours_traitement') NOT NULL,
  date_changement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  commentaire TEXT NULL,
  valeur_finale DECIMAL(15,2) NULL, -- Valeur finale si accepté
  id_compte_modificateur INT NULL,

  CONSTRAINT FK_historique_prospect FOREIGN KEY (id_prospect_fk) REFERENCES Prospect(id_prospect) ON DELETE CASCADE,
  CONSTRAINT FK_historique_compte FOREIGN KEY (id_compte_modificateur) REFERENCES Compte(id_compte) ON DELETE SET NULL
);

-- =====================================================
-- TABLES SUPPLÉMENTAIRES POUR FONCTIONNALITÉS AVANCÉES
-- =====================================================

--
-- Table pour les communications avec les prospects
--
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

--
-- Table pour les tâches de suivi
--
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

--
-- Table pour l'audit trail (journalisation des actions)
--
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

--
-- Table pour les sessions utilisateur
--
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

-- Index existant
CREATE INDEX idx_statut_prospect ON Prospect (statut_prospect);

-- Nouveaux index pour optimisation
CREATE INDEX idx_prospect_date_creation ON Prospect (date_creation);
CREATE INDEX idx_prospect_priorite ON Prospect (priorite);
CREATE INDEX idx_prospect_compte ON Prospect (id_compte_fk);
CREATE INDEX idx_prospect_statut_priorite ON Prospect (statut_prospect, priorite);
CREATE INDEX idx_compte_email ON Compte (email);
CREATE INDEX idx_compte_statut ON Compte (statut_compte);
CREATE INDEX idx_compte_role ON Compte (role_compte);
CREATE INDEX idx_historique_prospect_date ON Historique (id_prospect_fk, date_changement);
CREATE INDEX idx_communication_prospect_date ON Communication (id_prospect_fk, date_communication);
CREATE INDEX idx_tache_assignee_echeance ON Tache (id_compte_assigne, date_echeance);
CREATE INDEX idx_tache_statut ON Tache (statut_tache);
CREATE INDEX idx_audit_table_date ON Journal_Audit (table_concernee, date_action);
CREATE INDEX idx_session_compte_actif ON Session_Utilisateur (id_compte_fk, actif);

-- =====================================================
-- VUES POUR FACILITER LES REQUÊTES
-- =====================================================

--
-- Vue pour les prospects avec informations du gestionnaire
--
CREATE VIEW v_prospect_complet AS
SELECT
  p.id_prospect,
  p.nom_prospect,
  p.prenom_prospect,
  p.email_prospect,
  p.telephone_prospect,
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
LEFT JOIN Compte c ON p.id_compte_fk = c.id_compte;

--
-- Vue pour le tableau de bord des utilisateurs
--
CREATE VIEW v_dashboard_utilisateur AS
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
      'id_compte_fk', NEW.id_compte_fk
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

--
-- Trigger pour verrouillage de compte après tentatives échouées
--
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

--
-- Trigger pour nettoyer les sessions expirées
--
CREATE TRIGGER tr_session_cleanup
BEFORE INSERT ON Session_Utilisateur
FOR EACH ROW
BEGIN
  DELETE FROM Session_Utilisateur
  WHERE date_expiration < NOW() OR id_compte_fk = NEW.id_compte_fk;
END//

DELIMITER ;

-- =====================================================
-- PROCÉDURES STOCKÉES
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
  IN p_password VARCHAR(255),
  IN p_salt VARCHAR(32),
  IN p_role ENUM('admin', 'user', 'manager'),
  IN p_created_by INT
)
BEGIN
  DECLARE v_count INT DEFAULT 0;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- Vérifier l'unicité de l'email
  SELECT COUNT(*) INTO v_count FROM Compte WHERE email = p_email;
  IF v_count > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cette adresse email est déjà utilisée';
  END IF;

  -- Vérifier l'unicité du nom d'utilisateur
  SELECT COUNT(*) INTO v_count FROM Compte WHERE nom_utilisateur = p_nom_utilisateur;
  IF v_count > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ce nom d\'utilisateur est déjà utilisé';
  END IF;

  INSERT INTO Compte (nom_compte, prenom_compte, nom_utilisateur, email, password, salt, role_compte, created_by)
  VALUES (p_nom, p_prenom, p_nom_utilisateur, p_email, p_password, p_salt, p_role, p_created_by);

  -- Si c'est un admin, l'ajouter à la table Administrateur
  IF p_role = 'admin' THEN
    INSERT INTO Administrateur (id_admin, niveau_acces) VALUES (LAST_INSERT_ID(), 'admin');
  END IF;

  COMMIT;

  SELECT 'Compte créé avec succès' AS message, LAST_INSERT_ID() AS id_compte;
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
  DECLARE v_password_hash VARCHAR(255);
  DECLARE v_statut VARCHAR(20);
  DECLARE v_tentatives INT;
  DECLARE v_verrouille_jusqu DATETIME;

  -- Récupérer les informations du compte
  SELECT id_compte, password, statut_compte, tentatives_connexion, compte_verrouille_jusqu
  INTO v_id_compte, v_password_hash, v_statut, v_tentatives, v_verrouille_jusqu
  FROM Compte
  WHERE email = p_email;

  -- Vérifier si le compte existe
  IF v_id_compte IS NULL THEN
    SELECT 'Identifiants invalides' AS message, FALSE AS succes;
  -- Vérifier si le compte est verrouillé
  ELSEIF v_verrouille_jusqu IS NOT NULL AND v_verrouille_jusqu > NOW() THEN
    SELECT 'Compte verrouillé temporairement' AS message, FALSE AS succes;
  -- Vérifier le statut du compte
  ELSEIF v_statut != 'actif' THEN
    SELECT 'Compte inactif' AS message, FALSE AS succes;
  -- Vérifier le mot de passe
  ELSEIF p_password_hash = v_password_hash THEN
    -- Connexion réussie
    UPDATE Compte
    SET derniere_connexion = NOW(), tentatives_connexion = 0
    WHERE id_compte = v_id_compte;

    SELECT 'Connexion réussie' AS message, TRUE AS succes, v_id_compte AS id_compte;
  ELSE
    -- Mot de passe incorrect
    UPDATE Compte
    SET tentatives_connexion = tentatives_connexion + 1
    WHERE id_compte = v_id_compte;

    SELECT 'Identifiants invalides' AS message, FALSE AS succes;
  END IF;
END//

--
-- Procédure pour obtenir les statistiques des prospects
--
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

--
-- Procédure pour nettoyer les données obsolètes
--
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

--
-- Procédure pour assigner automatiquement des prospects
--
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
    WHERE c.role_compte IN ('user', 'manager') AND c.statut_compte = 'actif'
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

-- Note: La base de données est créée sans aucun compte par défaut
-- Le premier compte administrateur devra être créé manuellement
-- via l'application Python ou en utilisant la procédure stockée

-- =====================================================
-- ÉVÉNEMENTS PLANIFIÉS (optionnel)
-- =====================================================

-- Activer l'ordonnanceur d'événements si nécessaire
-- SET GLOBAL event_scheduler = ON;

-- Événement pour nettoyer automatiquement les données obsolètes
CREATE EVENT IF NOT EXISTS ev_nettoyage_quotidien
ON SCHEDULE EVERY 1 DAY
STARTS TIMESTAMP(CURRENT_DATE + INTERVAL 1 DAY, '02:00:00')
DO
  CALL sp_nettoyage_donnees();

/*
* Script optimisé terminé
* Fonctionnalités ajoutées :
* - Sécurité renforcée (hachage des mots de passe, gestion des sessions)
* - Tables supplémentaires (Communication, Tâche, Journal_Audit, Session_Utilisateur)
* - Vues pour faciliter les requêtes
* - Triggers pour automatisation
* - Procédures stockées pour les opérations complexes
* - Index optimisés pour les performances
* - Nettoyage automatique des données
*
* IMPORTANT: Aucun compte administrateur n'est créé automatiquement
* Le premier admin doit être créé via l'application ou manuellement
*/