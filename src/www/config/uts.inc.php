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

define("UTS_PLATFORM", "linux"); # or win32
define("UTS_DB_DSN", "mysql://uts:utspass@localhost/uts");
define("UTS_WIN_SCRIPTS_DIR", "c:\watched_folder");
define("UTS_DEFAULT_SERVER", "localhost");
define("UTS_SPMTABLE_PATH", "/usr/bin/spmtable");
define("LATITUDE", -27.70);    // decimal (negativo == sul)
define("LONGITUDE", -48.45); // decimal (negativo == oeste)

// oops.. daqui pra baixo complica...! o importante esta acima desta linha

define("NEED_SETUP", 0);

define("UTS_POINTING_TIME", 70);
define("UTS_CCD_READ_TIME", 25);

define("UTS_STATUS_UPDATE_RATE", 5);

define("UTS_USER_SEQ", "jdfkajdfkasfu"); // random 
define("UTS_TIME_SEQ", "jpoopwoemfif"); // random 

define("UTS_ERR_SEED", "Tsiolkovsky");

?>
