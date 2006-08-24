<?php

// UTS-www - Interface web para o UTS
// Copyright (C) 2003-2005 P. Henrique Silva <ph.silva@gmail.com>
// 
// This file is part of UTS-www.
// UTS-www is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
// 
// UTS-www is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
//

?><?php

session_start();

if(!$_SESSION['admin']) {
        session_destroy();
        Header("Location: index.php");
        exit(0);
}

require_once("root.php");
require_once(UTS."lib/db.php");
require_once(UTS."lib/erro.php");

// WARNING!!!
extract($_POST);


if($id) { // atualizar 

        $sql = "SELECT username FROM users WHERE username = '$username'";
        $res =& $db->query($sql);

        if($res->numRows() > 1) {  // o usuario ja existe e nao podera ser adicionado outro
                Header("Location: ". getError("user.php?id=$id", "O usu&aacute;rio <b>'$username'</b> j&aacute;¡ existe.<br>Por favor, escolha outro nome."));
                exit(10);
        }

        // checa privilegios de administrador
        if(!$root) {
                $root = 0;
        } else {
                $root = 1;
        }

        if(trim($passwd)) { // trocar a senha
                $sql = "UPDATE users SET nome = '$nome', username = '$username', root = $root, passwd = '" . md5($passwd) . "' WHERE id = $id";
        } else {
                $sql = "UPDATE users SET nome = '$nome', username = '$username', root = $root WHERE id = $id";
        }

        $res =& $db->query($sql);

        if (DB::isError($res)) {
                Header("Location: " . getError("user.php?id=$id", "Houve um erro ao tentar atualizar o registro. Tente novamente."));
                exit(4);
        }

        // BUG FIXME (quando nada eh modificado, ele retorna 0 a seguir, e parece que houve um erro, qdo na verdade nao houve!

        if($db->affectedRows()) {
                Header("Location: " . getMsg("user.php?id=$id", "Registro atualizado com sucesso."));
                exit(0);
        } else {
                Header("Location: " . getError("user.php?id=$id", "Houve um erro ao tentar atualizar o registro. Tente novamente."));
                exit(4);
        }



} else { // adicionar

        $sql = "SELECT username FROM users WHERE username = '$username'";
        $res =& $db->query($sql);

        $newID = $db->nextID(UTS_USER_SEQ);

        if($res->numRows()) {  // o usuario ja existe e nao podera ser adicionado outro
                Header("Location: ". getError("user.php?id=$id", "O usu&aacute;rio <b>'$username'</b> j&aacute; existe.<br>Por favor, escolha outro nome."));
                exit(10);
        }

        // checa privilegios de administrador
        if(!$root) {
                $root = 0;
        } else {
                $root = 1;
        }

        $sql = "INSERT INTO users VALUES($newID, '$nome', '$username', $root, '" . md5($passwd) . "')";

        $res =& $db->query($sql);

        if (DB::isError($res)) {
                Header("Location: " . getError("user.php?id=$newID", "Houve um erro ao tentar adicionar o usu&aacute;rio. Tente novamente."));
                exit(3);
        }

        if($db->affectedRows()) {
                Header("Location: " . getMsg("user.php?id=$newID", "Usu&aacute;rio '<b>$username</b>' adicionado com sucesso.."));
                exit(0);
        } else {
                Header("Location: " . getError("user.php?id=$newID", "Houve um erro ao tentar adicionar o usu&aacute;rio. Tente novamente."));
                exit(3);
        }

}

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title></title>
</head>
<body>
</body>
</html>
