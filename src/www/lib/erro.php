<?

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

?>
<?php

require_once("root.php");
require_once(UTS."config/uts.inc.php");

function getError($url, $msg) {

        if(strstr($url, "?")) {

                $url .= "&err=" . md5($msg.UTS_ERR_SEED) . "&str=" . urlencode($msg);


        } else {

                $url .= "?err=" . md5($msg.UTS_ERR_SEED) . "&str=" . urlencode($msg);

        }

        return $url;

}

function getMsg($url, $msg) {

	return getError($url, $msg);

}


function checkError($args) {

        if($args['err'] == md5(stripslashes($args['str'].UTS_ERR_SEED))) {
                return $args['str'];
        } else {
                return 0;
        }

}

function dumpError($class = "default") {

        if(isset($_GET['err']) && isset($_GET['str'])) {

                if(($msg = checkError($_GET))) {
?>

<div id="erro" class="<?=$class?>">
<?=stripslashes($msg)?>
</div>

<?
                }
        }

}

?>
