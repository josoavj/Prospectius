#!/usr/bin/env python3
"""
Système de Gestion des Prospects Prospectius
Auteur: Claude (basé sur la BD de josoavj)
Version: 1.0 - Système asynchrone complet

Fonctionnalités:
- Gestion asynchrone des prospects
- Authentification sécurisée
- Communications et tâches
- Tableaux de bord en temps réel
- Audit trail complet
"""

import asyncio
import aiomysql
import hashlib
import secrets
import json
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =====================================================
# ENUMS ET DATACLASSES
# =====================================================

class StatutProspect(Enum):
    ACCEPTE = "accepté"
    EN_ATTENTE = "en attente"
    REFUSE = "refusé"
    EN_COURS = "en_cours_traitement"


class PrioriteProspect(Enum):
    BASSE = "basse"
    NORMALE = "normale"
    HAUTE = "haute"
    URGENTE = "urgente"


class RoleCompte(Enum):
    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"


class StatutCompte(Enum):
    ACTIF = "actif"
    INACTIF = "inactif"
    SUSPENDU = "suspendu"


@dataclass
class Prospect:
    nom_prospect: str
    prenom_prospect: str
    email_prospect: str
    telephone_prospect: str
    adresse_prospect: str
    id_prospect: Optional[int] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    pays: str = "Madagascar"
    resume_prospect: Optional[str] = None
    statut_prospect: StatutProspect = StatutProspect.EN_ATTENTE
    priorite: PrioriteProspect = PrioriteProspect.NORMALE
    source_prospect: Optional[str] = None
    valeur_estimee: Optional[float] = None
    date_suivi_prevue: Optional[date] = None
    notes_internes: Optional[str] = None
    id_compte_fk: Optional[int] = None
    date_creation: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None


@dataclass
class Compte:
    nom_compte: str
    prenom_compte: str
    nom_utilisateur: str
    email: str
    password: str
    id_compte: Optional[int] = None
    salt: Optional[str] = None
    role_compte: RoleCompte = RoleCompte.USER
    statut_compte: StatutCompte = StatutCompte.ACTIF
    derniere_connexion: Optional[datetime] = None
    tentatives_connexion: int = 0
    compte_verrouille_jusqu: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class Communication:
    id_prospect_fk: int
    type_communication: str
    sujet: str
    id_compte_fk: int
    id_communication: Optional[int] = None
    contenu: Optional[str] = None
    date_communication: Optional[datetime] = None
    statut: str = "realise"


@dataclass
class Tache:
    id_prospect_fk: int
    titre: str
    date_echeance: date
    id_compte_assigne: int
    id_tache: Optional[int] = None
    description: Optional[str] = None
    statut_tache: str = "en_attente"
    priorite: str = "normale"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =====================================================
# GESTIONNAIRE DE BASE DE DONNÉES
# =====================================================

class DatabaseManager:
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.pool = None

    async def init_pool(self):
        """Initialise le pool de connexions"""
        try:
            self.pool = await aiomysql.create_pool(
                **self.db_config,
                minsize=5,
                maxsize=20,
                autocommit=False
            )
            logger.info("Pool de connexions initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du pool: {e}")
            raise

    async def close_pool(self):
        """Ferme le pool de connexions"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Pool de connexions fermé")

    async def execute_query(self, query: str, params: tuple = None, fetch: str = None):
        """Exécute une requête avec gestion des erreurs"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    await cursor.execute(query, params)

                    if fetch == 'one':
                        return await cursor.fetchone()
                    elif fetch == 'all':
                        return await cursor.fetchall()
                    elif fetch == 'many':
                        return await cursor.fetchmany()
                    else:
                        await conn.commit()
                        return cursor.lastrowid

                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Erreur lors de l'exécution de la requête: {e}")
                    raise

    async def execute_procedure(self, procedure_name: str, params: tuple = None):
        """Exécute une procédure stockée"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    await cursor.callproc(procedure_name, params or ())
                    result = await cursor.fetchall()
                    await conn.commit()
                    return result
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Erreur lors de l'exécution de la procédure {procedure_name}: {e}")
                    raise


# =====================================================
# GESTIONNAIRE D'AUTHENTIFICATION
# =====================================================

class AuthManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    @staticmethod
    def generate_salt() -> str:
        """Génère un salt aléatoire"""
        return secrets.token_hex(16)

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Hash un mot de passe avec le salt"""
        return hashlib.sha256((password + salt).encode()).hexdigest()

    async def create_user(self, compte: Compte, created_by: int = None) -> int:
        """Crée un nouvel utilisateur"""
        # Générer salt et hasher le mot de passe
        compte.salt = self.generate_salt()
        compte.password = self.hash_password(compte.password, compte.salt)

        try:
            result = await self.db.execute_procedure(
                'sp_creer_compte',
                (
                    compte.nom_compte,
                    compte.prenom_compte,
                    compte.nom_utilisateur,
                    compte.email,
                    compte.password,
                    compte.salt,
                    compte.role_compte.value,
                    created_by
                )
            )
            logger.info(f"Utilisateur créé: {compte.email}")
            return result[0]['id_compte']

        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            raise

    async def authenticate_user(self, email: str, password: str, ip_address: str) -> Dict[str, Any]:
        """Authentifie un utilisateur"""
        # Récupérer les informations du compte
        query = "SELECT id_compte, password, salt FROM Compte WHERE email = %s"
        user_data = await self.db.execute_query(query, (email,), fetch='one')

        if not user_data:
            return {"success": False, "message": "Identifiants invalides"}

        # Vérifier le mot de passe
        password_hash = self.hash_password(password, user_data['salt'])

        # Utiliser la procédure stockée pour l'authentification
        result = await self.db.execute_procedure(
            'sp_authentifier_utilisateur',
            (email, password_hash, ip_address)
        )

        return result[0] if result else {"success": False, "message": "Erreur d'authentification"}

    async def create_session(self, id_compte: int, ip_address: str, user_agent: str = None) -> str:
        """Crée une session utilisateur"""
        session_id = str(uuid.uuid4())
        expiration = datetime.now() + timedelta(hours=8)  # Session de 8h

        query = """
                INSERT INTO Session_Utilisateur
                    (id_session, id_compte_fk, adresse_ip, user_agent, date_expiration)
                VALUES (%s, %s, %s, %s, %s) \
                """

        await self.db.execute_query(
            query,
            (session_id, id_compte, ip_address, user_agent, expiration)
        )

        return session_id

    async def validate_session(self, session_id: str) -> Optional[int]:
        """Valide une session et retourne l'ID du compte"""
        query = """
                SELECT id_compte_fk \
                FROM Session_Utilisateur
                WHERE id_session = %s \
                  AND date_expiration > NOW() \
                  AND actif = TRUE \
                """

        result = await self.db.execute_query(query, (session_id,), fetch='one')
        return result['id_compte_fk'] if result else None


# =====================================================
# GESTIONNAIRE DES PROSPECTS
# =====================================================

class ProspectManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def create_prospect(self, prospect: Prospect, created_by: int) -> int:
        """Crée un nouveau prospect"""
        query = """
                INSERT INTO Prospect (nom_prospect, prenom_prospect, email_prospect, telephone_prospect, \
                                      adresse_prospect, code_postal, ville, pays, resume_prospect, \
                                      statut_prospect, priorite, source_prospect, valeur_estimee, \
                                      date_suivi_prevue, notes_internes, id_compte_fk, updated_by) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                """

        params = (
            prospect.nom_prospect, prospect.prenom_prospect, prospect.email_prospect,
            prospect.telephone_prospect, prospect.adresse_prospect, prospect.code_postal,
            prospect.ville, prospect.pays, prospect.resume_prospect,
            prospect.statut_prospect.value, prospect.priorite.value,
            prospect.source_prospect, prospect.valeur_estimee,
            prospect.date_suivi_prevue, prospect.notes_internes,
            prospect.id_compte_fk, created_by
        )

        prospect_id = await self.db.execute_query(query, params)
        logger.info(f"Prospect créé: {prospect.email_prospect} (ID: {prospect_id})")
        return prospect_id

    async def get_prospect(self, prospect_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un prospect par son ID"""
        query = "SELECT * FROM v_prospect_complet WHERE id_prospect = %s"
        return await self.db.execute_query(query, (prospect_id,), fetch='one')

    async def update_prospect_status(self, prospect_id: int, new_status: StatutProspect,
                                     updated_by: int, valeur_finale: float = None) -> bool:
        """Met à jour le statut d'un prospect"""
        query = """
                UPDATE Prospect
                SET statut_prospect = %s, \
                    updated_by      = %s, \
                    valeur_estimee  = COALESCE(%s, valeur_estimee)
                WHERE id_prospect = %s \
                """

        await self.db.execute_query(
            query,
            (new_status.value, updated_by, valeur_finale, prospect_id)
        )

        logger.info(f"Statut du prospect {prospect_id} mis à jour: {new_status.value}")
        return True

    async def search_prospects(self, filters: Dict[str, Any], user_id: int = None,
                               limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Recherche des prospects avec filtres"""
        conditions = ["1=1"]
        params = []

        # Filtrage par utilisateur si spécifié
        if user_id:
            conditions.append("id_compte_fk = %s")
            params.append(user_id)

        # Filtres dynamiques
        if filters.get('statut'):
            conditions.append("statut_prospect = %s")
            params.append(filters['statut'])

        if filters.get('priorite'):
            conditions.append("priorite = %s")
            params.append(filters['priorite'])

        if filters.get('date_debut'):
            conditions.append("date_creation >= %s")
            params.append(filters['date_debut'])

        if filters.get('date_fin'):
            conditions.append("date_creation <= %s")
            params.append(filters['date_fin'])

        if filters.get('recherche'):
            conditions.append("""
                (nom_prospect LIKE %s OR prenom_prospect LIKE %s 
                 OR email_prospect LIKE %s OR ville LIKE %s)
            """)
            search_term = f"%{filters['recherche']}%"
            params.extend([search_term] * 4)

        query = f"""
        SELECT * FROM v_prospect_complet 
        WHERE {' AND '.join(conditions)}
        ORDER BY date_creation DESC 
        LIMIT %s OFFSET %s
        """

        params.extend([limit, offset])

        return await self.db.execute_query(query, tuple(params), fetch='all')

    async def get_prospects_by_status(self, status: StatutProspect,
                                      user_id: int = None) -> List[Dict[str, Any]]:
        """Récupère les prospects par statut"""
        query = """
        SELECT * FROM v_prospect_complet 
        WHERE statut_prospect = %s
        """ + (" AND gestionnaire_id = %s" if user_id else "") + """
        ORDER BY priorite DESC, date_creation ASC
        """

        params = (status.value, user_id) if user_id else (status.value,)
        return await self.db.execute_query(query, params, fetch='all')

    async def assign_prospects_automatically(self) -> Dict[str, Any]:
        """Assigne automatiquement les prospects non assignés"""
        result = await self.db.execute_procedure('sp_assigner_prospects_automatiquement')
        return result[0] if result else {"message": "Aucun prospect à assigner"}


# =====================================================
# GESTIONNAIRE DES COMMUNICATIONS
# =====================================================

class CommunicationManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def add_communication(self, communication: Communication) -> int:
        """Ajoute une communication"""
        query = """
                INSERT INTO Communication (id_prospect_fk, type_communication, sujet, contenu, \
                                           date_communication, statut, id_compte_fk) \
                VALUES (%s, %s, %s, %s, %s, %s, %s) \
                """

        comm_id = await self.db.execute_query(
            query,
            (
                communication.id_prospect_fk,
                communication.type_communication,
                communication.sujet,
                communication.contenu,
                communication.date_communication or datetime.now(),
                communication.statut,
                communication.id_compte_fk
            )
        )

        logger.info(f"Communication ajoutée pour le prospect {communication.id_prospect_fk}")
        return comm_id

    async def get_communications(self, prospect_id: int) -> List[Dict[str, Any]]:
        """Récupère les communications d'un prospect"""
        query = """
                SELECT c.*, co.nom_compte, co.prenom_compte
                FROM Communication c
                         LEFT JOIN Compte co ON c.id_compte_fk = co.id_compte
                WHERE c.id_prospect_fk = %s
                ORDER BY c.date_communication DESC \
                """

        return await self.db.execute_query(query, (prospect_id,), fetch='all')

    async def schedule_communication(self, communication: Communication) -> int:
        """Programme une communication future"""
        communication.statut = "planifie"
        return await self.add_communication(communication)


# =====================================================
# GESTIONNAIRE DES TÂCHES
# =====================================================

class TaskManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def create_task(self, tache: Tache) -> int:
        """Crée une nouvelle tâche"""
        query = """
                INSERT INTO Tache (id_prospect_fk, titre, description, date_echeance, \
                                   statut_tache, priorite, id_compte_assigne) \
                VALUES (%s, %s, %s, %s, %s, %s, %s) \
                """

        task_id = await self.db.execute_query(
            query,
            (
                tache.id_prospect_fk,
                tache.titre,
                tache.description,
                tache.date_echeance,
                tache.statut_tache,
                tache.priorite,
                tache.id_compte_assigne
            )
        )

        logger.info(f"Tâche créée: {tache.titre}")
        return task_id

    async def update_task_status(self, task_id: int, new_status: str) -> bool:
        """Met à jour le statut d'une tâche"""
        query = "UPDATE Tache SET statut_tache = %s WHERE id_tache = %s"
        await self.db.execute_query(query, (new_status, task_id))
        logger.info(f"Statut de la tâche {task_id} mis à jour: {new_status}")
        return True

    async def get_user_tasks(self, user_id: int, include_completed: bool = False) -> List[Dict[str, Any]]:
        """Récupère les tâches d'un utilisateur"""
        query = """
                SELECT t.*, p.nom_prospect, p.prenom_prospect, p.email_prospect
                FROM Tache t
                         LEFT JOIN Prospect p ON t.id_prospect_fk = p.id_prospect
                WHERE t.id_compte_assigne = %s \
                """

        if not include_completed:
            query += " AND t.statut_tache != 'terminee'"

        query += " ORDER BY t.date_echeance ASC, t.priorite DESC"

        return await self.db.execute_query(query, (user_id,), fetch='all')

    async def get_overdue_tasks(self, user_id: int = None) -> List[Dict[str, Any]]:
        """Récupère les tâches en retard"""
        query = """
                SELECT t.*, p.nom_prospect, p.prenom_prospect, co.nom_compte, co.prenom_compte
                FROM Tache t
                         LEFT JOIN Prospect p ON t.id_prospect_fk = p.id_prospect
                         LEFT JOIN Compte co ON t.id_compte_assigne = co.id_compte
                WHERE t.date_echeance < CURDATE()
                  AND t.statut_tache IN ('en_attente', 'en_cours') \
                """

        params = ()
        if user_id:
            query += " AND t.id_compte_assigne = %s"
            params = (user_id,)

        query += " ORDER BY t.date_echeance ASC"

        return await self.db.execute_query(query, params, fetch='all')


# =====================================================
# GESTIONNAIRE DE STATISTIQUES
# =====================================================

class StatsManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def get_user_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Récupère les données du tableau de bord utilisateur"""
        query = "SELECT * FROM v_dashboard_utilisateur WHERE id_compte = %s"
        dashboard = await self.db.execute_query(query, (user_id,), fetch='one')

        if not dashboard:
            return {}

        # Ajouter les tâches en retard
        overdue_tasks = await TaskManager(self.db).get_overdue_tasks(user_id)
        dashboard['taches_en_retard_details'] = overdue_tasks

        return dashboard

    async def get_prospect_statistics(self, user_id: int = None,
                                      date_debut: date = None,
                                      date_fin: date = None) -> Dict[str, Any]:
        """Récupère les statistiques des prospects"""
        # Utiliser la procédure stockée
        if not date_debut:
            date_debut = date.today() - timedelta(days=30)
        if not date_fin:
            date_fin = date.today()

        result = await self.db.execute_procedure(
            'sp_statistiques_prospects',
            (user_id, date_debut, date_fin)
        )

        return result[0] if result else {}

    async def get_conversion_rates(self, user_id: int = None,
                                   days: int = 30) -> Dict[str, Any]:
        """Calcule les taux de conversion"""
        date_limite = date.today() - timedelta(days=days)

        query = """
                SELECT COUNT(*)                                                as total_prospects, \
                       COUNT(CASE WHEN statut_prospect = 'accepté' THEN 1 END) as acceptes, \
                       COUNT(CASE WHEN statut_prospect = 'refusé' THEN 1 END)  as refuses, \
                       AVG(DATEDIFF(updated_at, created_at))                   as duree_moyenne_traitement
                FROM Prospect
                WHERE date_creation >= %s \
                """

        params = [date_limite]
        if user_id:
            query += " AND id_compte_fk = %s"
            params.append(user_id)

        result = await self.db.execute_query(query, tuple(params), fetch='one')

        if result and result['total_prospects'] > 0:
            result['taux_conversion'] = (result['acceptes'] / result['total_prospects']) * 100
            result['taux_refus'] = (result['refuses'] / result['total_prospects']) * 100
        else:
            result = {'taux_conversion': 0, 'taux_refus': 0, 'duree_moyenne_traitement': 0}

        return result


# =====================================================
# GESTIONNAIRE PRINCIPAL
# =====================================================

class ProspectiusManager:
    """Gestionnaire principal du système Prospectius"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_manager = DatabaseManager(db_config)
        self.auth_manager = AuthManager(self.db_manager)
        self.prospect_manager = ProspectManager(self.db_manager)
        self.communication_manager = CommunicationManager(self.db_manager)
        self.task_manager = TaskManager(self.db_manager)
        self.stats_manager = StatsManager(self.db_manager)
        self.current_user_id = None
        self.current_session = None

    async def initialize(self):
        """Initialise le gestionnaire"""
        await self.db_manager.init_pool()
        logger.info("ProspectiusManager initialisé")

    async def close(self):
        """Ferme le gestionnaire"""
        await self.db_manager.close_pool()
        logger.info("ProspectiusManager fermé")

    async def login(self, email: str, password: str, ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """Connexion utilisateur"""
        auth_result = await self.auth_manager.authenticate_user(email, password, ip_address)

        if auth_result.get('succes'):
            self.current_user_id = auth_result['id_compte']
            self.current_session = await self.auth_manager.create_session(
                self.current_user_id, ip_address
            )
            return {
                "success": True,
                "message": "Connexion réussie",
                "session_id": self.current_session,
                "user_id": self.current_user_id
            }

        return {"success": False, "message": auth_result.get('message', 'Erreur de connexion')}

    async def validate_session(self, session_id: str) -> bool:
        """Valide une session"""
        user_id = await self.auth_manager.validate_session(session_id)
        if user_id:
            self.current_user_id = user_id
            self.current_session = session_id
            return True
        return False

    async def create_complete_prospect_workflow(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un workflow complet pour un nouveau prospect"""
        try:
            # 1. Créer le prospect
            prospect = Prospect(**prospect_data)
            prospect_id = await self.prospect_manager.create_prospect(prospect, self.current_user_id)

            # 2. Ajouter une communication initiale
            initial_comm = Communication(
                id_prospect_fk=prospect_id,
                type_communication="email",
                sujet="Premier contact",
                contenu="Premier contact établi avec le prospect",
                id_compte_fk=self.current_user_id
            )
            await self.communication_manager.add_communication(initial_comm)

            # 3. Créer une tâche de suivi
            follow_up_task = Tache(
                id_prospect_fk=prospect_id,
                titre=f"Suivi initial - {prospect.nom_prospect} {prospect.prenom_prospect}",
                description="Effectuer le suivi initial du prospect",
                date_echeance=date.today() + timedelta(days=3),
                id_compte_assigne=self.current_user_id,
                priorite=prospect.priorite.value
            )
            await self.task_manager.create_task(follow_up_task)

            return {
                "success": True,
                "prospect_id": prospect_id,
                "message": "Prospect créé avec workflow complet"
            }

        except Exception as e:
            logger.error(f"Erreur lors de la création du workflow prospect: {e}")
            return {"success": False, "message": str(e)}

    async def get_daily_report(self) -> Dict[str, Any]:
        """Génère un rapport quotidien"""
        try:
            # Statistiques générales
            stats = await self.stats_manager.get_user_dashboard(self.current_user_id)

            # Tâches du jour
            today_tasks = await self.task_manager.get_user_tasks(self.current_user_id)
            today_tasks_filtered = [
                task for task in today_tasks
                if task['date_echeance'] <= date.today()
            ]

            # Prospects à haute priorité
            high_priority_prospects = await self.prospect_manager.search_prospects(
                {"priorite": "haute"},
                self.current_user_id,
                limit=10
            )

            # Tâches en retard
            overdue_tasks = await self.task_manager.get_overdue_tasks(self.current_user_id)

            return {
                "date_rapport": date.today(),
                "statistiques_generales": stats,
                "taches_du_jour": today_tasks_filtered,
                "prospects_haute_priorite": high_priority_prospects,
                "taches_en_retard": overdue_tasks,
                "alertes": len(overdue_tasks) + len(
                    [p for p in high_priority_prospects if p['statut_prospect'] == 'en attente'])
            }

        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            return {"error": str(e)}

    async def process_batch_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Traite des opérations en lot"""
        results = []
        errors = []

        for operation in operations:
            try:
                op_type = operation.get('type')
                op_data = operation.get('data', {})

                if op_type == 'update_prospect_status':
                    await self.prospect_manager.update_prospect_status(
                        op_data['prospect_id'],
                        StatutProspect(op_data['status']),
                        self.current_user_id,
                        op_data.get('valeur_finale')
                    )
                    results.append(f"Prospect {op_data['prospect_id']} mis à jour")

                elif op_type == 'complete_task':
                    await self.task_manager.update_task_status(
                        op_data['task_id'],
                        'terminee'
                    )
                    results.append(f"Tâche {op_data['task_id']} terminée")

                elif op_type == 'add_communication':
                    comm = Communication(**op_data)
                    comm.id_compte_fk = self.current_user_id
                    await self.communication_manager.add_communication(comm)
                    results.append(f"Communication ajoutée pour prospect {comm.id_prospect_fk}")

                elif op_type == 'assign_prospect':
                    await self.prospect_manager.update_prospect_status(
                        op_data['prospect_id'],
                        StatutProspect.EN_COURS,
                        self.current_user_id
                    )
                    # Mettre à jour l'assignation
                    query = "UPDATE Prospect SET id_compte_fk = %s WHERE id_prospect = %s"
                    await self.db_manager.execute_query(
                        query,
                        (op_data['assigned_to'], op_data['prospect_id'])
                    )
                    results.append(f"Prospect {op_data['prospect_id']} assigné")

            except Exception as e:
                errors.append(f"Erreur dans l'opération {op_type}: {str(e)}")

        return {
            "success": len(errors) == 0,
            "processed": len(results),
            "results": results,
            "errors": errors
        }


# =====================================================
# UTILITAIRES ET HELPERS
# =====================================================

class ProspectiusUtils:
    """Utilitaires pour le système Prospectius"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Valide un email"""
        import re
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valide un numéro de téléphone"""
        import re
        pattern = r'^[0-9+\-\s()]+
        return re.match(pattern, phone) is not None

    @staticmethod
    def format_currency(amount: float, currency: str = "MGA") -> str:
        """Formate un montant en devise"""
        return f"{amount:,.2f} {currency}"

    @staticmethod
    def calculate_priority_score(prospect: Dict[str, Any]) -> int:
        """Calcule un score de priorité"""
        score = 0

        # Valeur estimée
        if prospect.get('valeur_estimee'):
            if prospect['valeur_estimee'] > 1000000:  # 1M MGA
                score += 30
            elif prospect['valeur_estimee'] > 500000:  # 500K MGA
                score += 20
            elif prospect['valeur_estimee'] > 100000:  # 100K MGA
                score += 10

        # Priorité définie
        priority_scores = {
            'urgente': 40,
            'haute': 30,
            'normale': 20,
            'basse': 10
        }
        score += priority_scores.get(prospect.get('priorite', 'normale'), 20)

        # Ancienneté (plus ancien = plus prioritaire)
        if prospect.get('date_creation'):
            days_old = (date.today() - prospect['date_creation']).days
            if days_old > 7:
                score += 15
            elif days_old > 3:
                score += 10
            elif days_old > 1:
                score += 5

        return score

    @staticmethod
    def generate_prospect_report(prospects: List[Dict[str, Any]]) -> str:
        """Génère un rapport textuel des prospects"""
        if not prospects:
            return "Aucun prospect à afficher"

        report = f"=== RAPPORT PROSPECTS ({len(prospects)} prospects) ===\n\n"

        for prospect in prospects:
            score = ProspectiusUtils.calculate_priority_score(prospect)
            report += f"• {prospect['nom_prospect']} {prospect['prenom_prospect']}\n"
            report += f"  Email: {prospect['email_prospect']}\n"
            report += f"  Statut: {prospect['statut_prospect']} | Priorité: {prospect['priorite']}\n"

            if prospect.get('valeur_estimee'):
                report += f"  Valeur estimée: {ProspectiusUtils.format_currency(prospect['valeur_estimee'])}\n"

            report += f"  Score priorité: {score}/100\n"

            if prospect.get('gestionnaire_nom'):
                report += f"  Gestionnaire: {prospect['gestionnaire_nom']} {prospect['gestionnaire_prenom']}\n"

            report += f"  Créé le: {prospect.get('date_creation', 'N/A')}\n\n"

        return report


# =====================================================
# EXEMPLE D'UTILISATION
# =====================================================

async def exemple_utilisation():
    """Exemple d'utilisation du système Prospectius"""

    # Configuration de la base de données
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'votre_utilisateur',
        'password': 'votre_mot_de_passe',
        'db': 'Prospectius',
        'charset': 'utf8mb4'
    }

    # Initialiser le gestionnaire
    manager = ProspectiusManager(DB_CONFIG)

    try:
        await manager.initialize()

        # === AUTHENTIFICATION ===
        print("=== Test d'authentification ===")
        login_result = await manager.login(
            "admin@prospectius.com",
            "motdepasse123",
            "192.168.1.100"
        )
        print(f"Connexion: {login_result}")

        if not login_result['success']:
            print("Échec de connexion, arrêt du test")
            return

        # === CRÉATION D'UN PROSPECT ===
        print("\n=== Création d'un prospect ===")
        prospect_data = {
            'nom_prospect': 'Rakoto',
            'prenom_prospect': 'Jean',
            'email_prospect': 'jean.rakoto@email.com',
            'telephone_prospect': '+261341234567',
            'adresse_prospect': '123 Avenue de l\'Indépendance',
            'ville': 'Antananarivo',
            'code_postal': '101',
            'resume_prospect': 'Prospect intéressé par nos services de conseil',
            'priorite': PrioriteProspect.HAUTE,
            'valeur_estimee': 750000.00,
            'source_prospect': 'web'
        }

        creation_result = await manager.create_complete_prospect_workflow(prospect_data)
        print(f"Création prospect: {creation_result}")

        # === RECHERCHE DE PROSPECTS ===
        print("\n=== Recherche de prospects ===")
        prospects = await manager.prospect_manager.search_prospects(
            {'statut': 'en attente'},
            manager.current_user_id,
            limit=5
        )

        print(f"Prospects trouvés: {len(prospects)}")
        for prospect in prospects:
            print(f"- {prospect['nom_prospect']} {prospect['prenom_prospect']} ({prospect['statut_prospect']})")

        # === TABLEAU DE BORD ===
        print("\n=== Tableau de bord ===")
        dashboard = await manager.stats_manager.get_user_dashboard(manager.current_user_id)
        print("Dashboard:")
        for key, value in dashboard.items():
            if not key.endswith('_details'):
                print(f"  {key}: {value}")

        # === TÂCHES EN RETARD ===
        print("\n=== Tâches en retard ===")
        overdue_tasks = await manager.task_manager.get_overdue_tasks(manager.current_user_id)
        print(f"Tâches en retard: {len(overdue_tasks)}")

        # === RAPPORT QUOTIDIEN ===
        print("\n=== Rapport quotidien ===")
        daily_report = await manager.get_daily_report()
        print(f"Alertes: {daily_report.get('alertes', 0)}")
        print(f"Tâches du jour: {len(daily_report.get('taches_du_jour', []))}")

        # === OPÉRATIONS EN LOT ===
        print("\n=== Opérations en lot ===")
        if creation_result['success']:
            batch_operations = [
                {
                    'type': 'add_communication',
                    'data': {
                        'id_prospect_fk': creation_result['prospect_id'],
                        'type_communication': 'telephone',
                        'sujet': 'Appel de suivi',
                        'contenu': 'Appel effectué avec succès'
                    }
                },
                {
                    'type': 'update_prospect_status',
                    'data': {
                        'prospect_id': creation_result['prospect_id'],
                        'status': 'en_cours_traitement'
                    }
                }
            ]

            batch_result = await manager.process_batch_operations(batch_operations)
            print(f"Opérations en lot: {batch_result}")

        # === STATISTIQUES AVANCÉES ===
        print("\n=== Statistiques avancées ===")
        stats = await manager.stats_manager.get_prospect_statistics(manager.current_user_id)
        print("Statistiques:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        conversion_rates = await manager.stats_manager.get_conversion_rates(manager.current_user_id)
        print(f"Taux de conversion: {conversion_rates.get('taux_conversion', 0):.2f}%")

        # === GÉNÉRATION DE RAPPORT ===
        print("\n=== Rapport des prospects ===")
        prospects_report = ProspectiusUtils.generate_prospect_report(prospects[:3])
        print(prospects_report)

    except Exception as e:
        logger.error(f"Erreur dans l'exemple: {e}")

    finally:
        await manager.close()


# =====================================================
# TÂCHES AUTOMATISÉES
# =====================================================

class AutomatedTasks:
    """Tâches automatisées pour le système"""

    def __init__(self, manager: ProspectiusManager):
        self.manager = manager

    async def daily_maintenance(self):
        """Maintenance quotidienne"""
        try:
            # Nettoyer les données obsolètes
            await self.manager.db_manager.execute_procedure('sp_nettoyage_donnees')

            # Assigner automatiquement les prospects
            await self.manager.prospect_manager.assign_prospects_automatically()

            logger.info("Maintenance quotidienne effectuée")

        except Exception as e:
            logger.error(f"Erreur lors de la maintenance: {e}")

    async def send_daily_notifications(self):
        """Envoie les notifications quotidiennes"""
        try:
            # Récupérer tous les utilisateurs actifs
            query = "SELECT id_compte, email, nom_compte, prenom_compte FROM Compte WHERE statut_compte = 'actif'"
            users = await self.manager.db_manager.execute_query(query, fetch='all')

            for user in users:
                # Générer le rapport pour chaque utilisateur
                self.manager.current_user_id = user['id_compte']
                daily_report = await self.manager.get_daily_report()

                # Ici, vous pourriez intégrer l'envoi d'emails
                # avec les données du rapport
                print(f"Notification envoyée à {user['email']}: {daily_report.get('alertes', 0)} alertes")

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des notifications: {e}")

    async def run_scheduled_tasks(self):
        """Exécute les tâches programmées"""
        while True:
            try:
                # Maintenance quotidienne à 2h du matin
                now = datetime.now()
                if now.hour == 2 and now.minute == 0:
                    await self.daily_maintenance()

                # Notifications à 8h du matin
                if now.hour == 8 and now.minute == 0:
                    await self.send_daily_notifications()

                # Attendre 1 minute
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Erreur dans les tâches programmées: {e}")
                await asyncio.sleep(300)  # Attendre 5 minutes en cas d'erreur


# =====================================================
# API REST SIMPLE (OPTIONNEL)
# =====================================================

class SimpleAPI:
    """API REST simple pour le système"""

    def __init__(self, manager: ProspectiusManager):
        self.manager = manager

    async def handle_request(self, method: str, endpoint: str, data: Dict[str, Any] = None,
                             headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Gestionnaire simple de requêtes API"""
        try:
            # Vérification de session
            session_id = headers.get('Authorization', '').replace('Bearer ', '')
            if not await self.manager.validate_session(session_id):
                return {"error": "Session invalide", "code": 401}

            # Routes principales
            if method == 'GET':
                if endpoint == '/prospects':
                    filters = data or {}
                    prospects = await self.manager.prospect_manager.search_prospects(
                        filters, self.manager.current_user_id
                    )
                    return {"prospects": prospects}

                elif endpoint == '/dashboard':
                    dashboard = await self.manager.stats_manager.get_user_dashboard(
                        self.manager.current_user_id
                    )
                    return {"dashboard": dashboard}

                elif endpoint == '/tasks':
                    tasks = await self.manager.task_manager.get_user_tasks(
                        self.manager.current_user_id
                    )
                    return {"tasks": tasks}

            elif method == 'POST':
                if endpoint == '/prospects':
                    result = await self.manager.create_complete_prospect_workflow(data)
                    return result

                elif endpoint == '/communications':
                    comm = Communication(**data)
                    comm.id_compte_fk = self.manager.current_user_id
                    comm_id = await self.manager.communication_manager.add_communication(comm)
                    return {"success": True, "communication_id": comm_id}

                elif endpoint == '/tasks':
                    tache = Tache(**data)
                    tache.id_compte_assigne = self.manager.current_user_id
                    task_id = await self.manager.task_manager.create_task(tache)
                    return {"success": True, "task_id": task_id}

            elif method == 'PUT':
                if endpoint.startswith('/prospects/') and endpoint.endswith('/status'):
                    prospect_id = int(endpoint.split('/')[2])
                    new_status = StatutProspect(data['status'])
                    await self.manager.prospect_manager.update_prospect_status(
                        prospect_id, new_status, self.manager.current_user_id
                    )
                    return {"success": True}

                elif endpoint.startswith('/tasks/') and endpoint.endswith('/status'):
                    task_id = int(endpoint.split('/')[2])
                    await self.manager.task_manager.update_task_status(
                        task_id, data['status']
                    )
                    return {"success": True}

            return {"error": "Endpoint non trouvé", "code": 404}

        except Exception as e:
            logger.error(f"Erreur API {method} {endpoint}: {e}")
            return {"error": str(e), "code": 500}


# =====================================================
# POINT D'ENTRÉE PRINCIPAL
# =====================================================

async def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage du système Prospectius...")

    # Configuration de votre base de données
    # REMPLACEZ par vos vraies informations de connexion
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',  # Remplacez par votre utilisateur
        'password': 'password',  # Remplacez par votre mot de passe
        'db': 'Prospectius',
        'charset': 'utf8mb4'
    }

    # Exécuter l'exemple
    await exemple_utilisation()

    print("✅ Test terminé avec succès!")


if __name__ == "__main__":
    # Exécuter le programme principal
    asyncio.run(main())