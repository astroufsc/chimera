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

if(!$_SESSION['user']) {
        session_destroy();
        Header("Location: index.php");
}

require_once("root.php");
require_once(UTS."config/uts.inc.php");
require_once(UTS."lib/erro.php");

if(UTS_PLATFORM == "linux")
        $action = "apontar-uts.php";
else if(UTS_PLATFORM == "win32")
        $action = "apontar-orch.php";
else
        $action = "apontar-uts.php";


if(isset($_GET['ra'])) {

  $ra = split(":", $_GET['ra']);

}

if(isset($_GET['dec'])) {

  $dec = split(":", $_GET['dec']);

}


?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&oacute;pios na Escola ::: Apontar e integrar</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="css/uts.css" rel="stylesheet" type="text/css">
<script src="js/nicetitle.js" type="text/javascript">
</script>
<script src="js/jsval.js" type="text/javascript" language=
"javascript">
</script>
<script src="js/uts.js" type="text/javascript" language=
"javascript">
</script>
<script type="text/javascript" language="javascript">

        function initValidation() {

                var form = document.forms['apontar'];

                form.ra_h.required = 1;
                form.ra_h.realname = "Ascensão reta";
                form.ra_h.err = "Você deve digitar uma Ascensão reta.";
                form.ra_h.regexp = /^\d{1,2}/;
//              form.ra_h.minvalue = 0;
//              form.ra_h.maxvalue = 24;

                form.ra_m.required = 1;
                form.ra_m.realname = "Ascensão reta";
                form.ra_m.err = "Você deve digitar uma Ascensão reta.";
                form.ra_m.regexp = /^\d{1,2}/;
//              form.ra_m.minvalue = 0;
//              form.ra_m.maxvalue = 60;

                form.ra_s.required = 1;
                form.ra_s.realname = "Ascensão reta";
                form.ra_s.err = "Você deve digitar uma Ascensão reta.";
                form.ra_s.regexp = /^\d{1,2}/;
//              form.ra_s.minvalue = 0;
//              form.ra_s.maxvalue = 60;

                form.dec_g.required = 1;
                form.dec_g.realname =  "Declinação";
                form.dec_g.err = "Você deve digitar uma Declinação.";
                form.dec_g.regexp = /^[+-]?\d{1,2}/;
//              form.dec_g.minvalue = -12;
//              form.dec_g.maxvalue = 12;

                form.dec_m.required = 1;
                form.dec_m.realname =  "Declinação";
                form.dec_m.err = "Você deve digitar uma Declinação.";
                form.dec_m.regexp = /^\d{1,2}/;
//              form.dec_m.minvalue = 0;
//              form.dec_m.maxvalue = 60;

                form.dec_s.required = 1;
                form.dec_s.realname =  "Declinação";
                form.dec_s.err = "Você deve digitar uma Declinação.";
                form.dec_s.regexp = /^\d{1,2}\.?\d*$/;
//              form.dec_s.minvalue = 0;
//              form.dec_s.maxvalue = 60;

//              form.dec.required = 1;
//              form.dec.regexp = /^[+-]?\d{1,2}:\d{1,2}:\d{1,2}\.?\d*$/;
//              form.dec.realname = "Declinação";
//              form.dec.err = "Você deve digitar uma Declinação.";

//              form.num_exp.required = 1;
//              form.num_exp.regexp = /\d{1,3}/;
//              form.num_exp.minvalue = 0;
//              form.num_exp.maxvalue = 100;
//              form.num_exp.realname = "Número de exposições";
//              form.num_exp.err = "Você deve digitar um valor para o número de exposições.";

//              form.exp_time.required = 1;
//              form.exp_time.regexp = /\d{1,3}/;
//              form.exp_time.minvalue = 0; // FIXME
//              form.exp_time.maxvalue = 1000;
//              form.exp_time.realname = "Tempo de exposição";
//              form.exp_time.err = "Você deve digitar um valor para o tempo de exposição.";


        }

</script>
</head>
<body onload="initValidation();">
<center>
<div id="titulo">Telesc&oacute;pios na Escola</div>
<br>
<h3>Apontar e Integrar</h3>
</center>
<?php dumpError(); ?>
<div class="ajuda"><big>Procedimento</big>
<p>Preencha o formul&aacute;rio abaixo, clique em 'Observar' e
aguarde. Ser&aacute; exibida uma p&aacute;gina com
informa&ccedil;&otilde;es sobre o andamento da
observa&ccedil;&atilde;o.<br>
Posicione o cursor sobre um dos campos abaixo par obter mais
informa&ccedil;&otilde;es.</p>
</div>
<br>
<form name="apontar" action="<?=$action?>" method="get"
onsubmit="return validateStandard(this, 'error');" id="apontar">
<input type="hidden" name="epoca" value="J2000">
<table align="center">
<tr>
<td><a href="javascript:void();" title="Objeto" id=
"Digite o nome do objeto que ser&aacute; observado." name=
"Digite o nome do objeto que ser&aacute; observado.">Objeto</a>:</td>
<td><input type="text" name="obj" maxlenght="40" class="txt"
tabindex="1" value="<?=$_GET['obj']?>"></td>
<td></td>
</tr>
<tr>
<td><a href="javascript:void();" title="Ascens&atilde;o reta" id=
"Digite a ascens&atilde;o reta usando a forma hor&aacute;ria 'hora minutos segundos'"
name=
"Digite a ascens&atilde;o reta usando a forma hor&aacute;ria 'hora minutos segundos'">
Ascens&atilde;o reta (RA)</a></td>
<td><input type="text" name="ra_h" maxlenght="3" class="txt"
tabindex="2" size="3" value="<?=$ra[0]?>"> <input type="text"
name="ra_m" maxlenght="2" class="txt" tabindex="2" size="2" value=
"<?=$ra[1]?>"> <input type="text" name="ra_s" maxlenght="2"
class="txt" tabindex="2" size="2" value="<?=$ra[2]?>"></td>
</tr>
<tr>
<td><a href="javascript:void();" title="Declina&ccedil;&atilde;o"
id=
"Digite a declina&ccedil;&atilde;o em graus, minutos e segundos (-gg mm ss). Graus negativos referem-se a declina&ccedil;&atilde;o sul."
name=
"Digite a declina&ccedil;&atilde;o em graus, minutos e segundos (-gg mm ss). Graus negativos referem-se a declina&ccedil;&atilde;o sul.">
Declina&ccedil;&atilde;o (DEC)</a>:</td>
<td><input type="text" name="dec_g" maxlenght="3" class="txt"
tabindex="2" size="3" value="<?=$dec[0]?>"> <input type=
"text" name="dec_m" maxlenght="2" class="txt" tabindex="2" size="2"
value="<?=$dec[1]?>"> <input type="text" name="dec_s"
maxlenght="2" class="txt" tabindex="2" size="2" value=
"<?=$dec[2]?>"></td>
<td></td>
</tr>
<tr>
<td><a href="javascript:void();" title=
"N&uacute;mero de exposi&ccedil;&otilde;es" id=
"Digite a quantidade de imagens que deseja obter desta posi&ccedil;&atilde;o do c&eacute;u."
name=
"Digite a quantidade de imagens que deseja obter desta posi&ccedil;&atilde;o do c&eacute;u.">
N&uacute;mero de exposi&ccedil;&otilde;es:</a>:</td>
<td><input type="text" name="num_exp" maxlenght="20" class="txt"
tabindex="4" value="<?=$_GET['num_exp']?>"></td>
<td></td>
</tr>
<tr>
<td><a href="javascript:void();" title=
"Tempo de exposi&ccedil;&atilde;o" id=
"Digite a quantidade de tempo, em segundos, que deseja integrar em cada exposi&ccedil;&atilde;o."
name=
"Digite a quantidade de tempo, em segundos, que deseja integrar em cada exposi&ccedil;&atilde;o.">
Tempo de exposi&ccedil;&atilde;o</a>:</td>
<td><input type="text" name="exp_time" maxlenght="20" class="txt"
tabindex="5" value="<?=$_GET['exp_time']?>"></td>
<td></td>
</tr>
<tr>
<td><a href="javascript:void();" title="Filtro" id=
"Escolha o filtro que deseja usar neste conjunto de exposi&ccedil;&otilde;es."
name=
"Escolha o filtro que deseja usar neste conjunto de exposi&ccedil;&otilde;es.">
Filtro</a>:</td>
<td><select name="filtro" class="txt" tabindex="6">
<option value="5">Clear</option>
<option value="2">Azul</option>
<option value="3">Verde</option>
<option value="1">Vermelho</option>
<option value="4">Lunar</option>
</select></td>
<td></td>
</tr>
<tr>
<td colspan="3">&nbsp;</td>
</tr>
<tr>
<td align="center">
<div align="left"></div>
</td>
<td align="center">
<div align="left"><input type="submit" name="get_now" value=
"Observar" tabindex="6"></div>
</td>
</tr>
</table>
<br>
<p align="center"><a href="home.php">::: voltar :::</a></p>
</form>
</body>
</html>
