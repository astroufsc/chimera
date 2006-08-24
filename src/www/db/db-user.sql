-- create user and give privileges

GRANT USAGE ON * . * TO '{$uts_mysql_user}'@'{$uts_mysql_server}' IDENTIFIED BY '{$uts_mysql_user_pass}' WITH MAX_QUERIES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0;

GRANT SELECT , INSERT , UPDATE , DELETE , CREATE , DROP , INDEX , ALTER ON '{$uts_mysql_db}' . * TO '{$uts_mysql_user}'@'{$uts_mysql_server}';

FLUSH PRIVILEGES;
