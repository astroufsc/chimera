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

// check if setup is needed
require_once("root.php");
require_once(UTS."config/uts.inc.php");
require_once(UTS."lib/erro.php");
require_once(UTS."lib/astro.php");

session_start();

if(!$_SESSION['user']) {
        session_destroy();
        Header("Location: index.php");
}

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&oacute;pios na Escola - C&eacute;u</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="css/uts.css" rel="stylesheet" type="text/css">
<script src="js/uts.js" type="text/javascript" language=
"javascript">
</script>
</head>
<body style="background-color: white; text-align: center">
<a href="home.php">:: voltar ::</a><br><br>
<img src=
"http://www.heavens-above.com/skychart.aspx?Lat=<?=LATITUDE?>&amp;Lng=<?=LONGITUDE?>&amp;Time=<?=mjd(time())?>&amp;BW=1&amp;size=600&amp;SL=1&amp;SN=1">
<pre style="color: gray">
Developed and maintained by Chris Peat, Heavens-Above GmbH
</pre>
</body>
</html>
