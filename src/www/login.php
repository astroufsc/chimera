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

require_once("root.php");

require_once(UTS."lib/db.php");
require_once(UTS."lib/erro.php");
require_once(UTS."lib/utils.php");

// o usuรกrio existe?
$sql = "SELECT * FROM users WHERE username = '" . trim($_POST['user']) . "'";
$res =& $db->query($sql);

if(PEAR::isError($res)) { // DB error
        Header("Location: " . getError("index.php", "N&atilde;o foi poss&iacute;vel contatar o observat&oacute;rio. Consulte o respons&aacute;vel."));
        exit(2);
}

if(!$res->numRows()) { // usuแrio nใo encontrado
        Header("Location: " . getError("index.php", "Senha ou usu&aacute;rio inv&aacute;lidos"));
        exit(1);
}

// OK.. usuario encontrado, checar senha
$res->fetchInto($data, DB_FETCHMODE_ASSOC);

if($data['passwd'] == md5(trim($_POST['pass']))) { // OK, senha confere

        // checa se ้ administrador, se for, deixa passar, mesmo sem checar tempo e unicidade da sessao
        if($data['root'] == 1) {
                doLogin($data['nome'], $data['username'], $data['id'], 1, $db);
                exit(0);
        }

        if(userAllowed($data['id'], $db)) { // eu sei! poderia usar && (AND), mas para poder especificar o erro corretamente uso dois if's

                if(userUniq($data['id'], $db)) {
                        doLogin($data['nome'], $data['username'], $data['id'], 0, $db);
                        exit(0);
                } else {
                        Header("Location: " . getError("index.php", "J&aacute; h&aacute; uma sess&atilde;o em andamento para este usu&aacute;rio."));
                        exit(3);
                }

        } else {

                Header("Location: " . getError("index.php", "Voc&ecirc; n&atilde;o possu&iacute; tempo alocado para este momento. Consulte o respons&aacute;vel."));
                exit(3);

        }

} else { /// OOps, senha errada.
        Header("Location: " . getError("index.php", "Senha ou usu&aacute;rio inv&aacute;lidos."));
        exit(1);
}

?>