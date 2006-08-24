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

// logout user and delete session variables

session_start();

if(!$_SESSION['user']) {
        session_destroy();
        Header("Location: index.php");
}

require_once("root.php");
require_once(UTS."lib/db.php");
require_once(UTS."lib/erro.php");

if(!$_SESSION['root']) {

        $sql = "DELETE FROM logged WHERE id = " . $_SESSION['user_id'];
        $res =& $db->query($sql);

        if(PEAR::isError($res) || !$db->affectedRows()) {
                Header("Location " . getError("home.php", "Não foi possível efetuar o logout, aguarde mais alguns instantes e tente novamente."));
        } else {
                session_destroy();
                Header("Location: index.php");
        }

} else {
 
        session_destroy();
        Header("Location: index.php");

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
