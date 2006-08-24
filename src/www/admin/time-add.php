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

$newID = $db->nextID(UTS_TIME_SEQ);

$inicio = mktime($inicio_hora, $inicio_min, 0, $inicio_mes, $inicio_dia, $inicio_ano);
$fim = mktime($fim_hora, $fim_min, 0, $fim_mes, $fim_dia, $fim_ano);


if($inicio > $fim) {
        Header("Location: " . getError("user.php?id=$id", "O per&iacute;odo selecionado &eacute; inv&aacute;lido (<i>ele termina antes de come&ccedil;ar :-)</i>"));
        exit(3);
} else if($inicio == $fim) {
        Header("Location: " . getError("user.php?id=$id", "O per&iacute;odo selecionado &eacute; inv&aacute;lido  (<i>ele n&atilde;o dura nem 1 segundo :-)</i>"));
        exit(3);
}

// checa possivel conflito

$sql = "SELECT inicio, fim FROM user_sched WHERE ( (inicio >= $inicio AND inicio <= $fim) OR (fim >= $inicio AND fim <= $fim) )";

$res =& $db->query($sql);

if (DB::isError($res)) {
        Header("Location: " . getError("user.php?id=$id", "Houve um erro ao tentar alocar tempo ao usu&aacute;rio. Tente novamente."));
        exit(1);
}       

if($res->numRows()) {
  Header("Location: " . getError("user.php?id=$id", "O per&iacute;odo selecionado j&aacute; est&aacute; ocupado."));  // conflito
        exit(0);
}

// sem conflitos, continua...
        
$sql = "INSERT INTO user_sched VALUES($id, $newID, $inicio, $fim)";

$res =& $db->query($sql);

if (DB::isError($res)) {
        Header("Location: " . getError("user.php?id=$id", "Houve um erro ao tentar alocar tempo ao usu&aacute;rio. Tente novamente."));
        exit(1);
}

if($db->affectedRows()) {
        Header("Location: " . getMsg("user.php?id=$id", "O per&iacute;odo foi alocado com sucesso."));
        exit(0);
} else {
        Header("Location: " . getError("user.php?id=$id", "Houve um erro ao tentar alocar tempo ao usu&aacute;rio. Tente novamente."));
        exit(1);
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
