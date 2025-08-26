/*
* Script pour la création d'un compte à utiliser uniquement pour Prospectius
*/
CREATE USER 'Prospectius'@'localhost' IDENTIFIED BY 'Prospectius';
GRANT ALL PRIVILEGES ON Prospectius.* TO 'Prospectius'@'localhost';
FLUSH PRIVILEGES ;

/*
* Modifié le 26 Août 2025
*/