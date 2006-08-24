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
<?

require_once("root.php");
require_once(UTS."config/uts.inc.php"); 

require_once("Socket.php");

class Sec {
  
  var $socket;

  var $name;
  var $type;
  var $props;
  var $interactive = TRUE;

  function Sec($name, $type, $props) {
    $this->socket = null;
    $this->name = $name;
    $this->type = $type;
    $this->props = $props;
  }

  function connect($addr = null, $port = null) {
    if($this->socket != null) {
      $this->disconnect();
    }

    $this->socket = new Socket();

    if(!$addr || !$port) {
      $addr = UTS_DEFAULT_SERVER;
      $servers = getServers($addr);
      $port = $servers[$this->name . $this->type];
    }

    if(!$this->socket->connect($addr, $port)) {
      return FALSE;
    }

    // check SERVER_FULL
    $full = $this->socket->read();
    $full = trim($this->removeNULL($full));

    if($full == "SERVER_FULL") {
	return FALSE;
    }

    // ident     
    $this->socket->write($this->appendNULL("IDENT INSTRUMENT"));

    $str = $this->socket->read();
    $str = $this->removeNULL($str);

    if($str == "ERROR") {
      return FALSE;
    } else {
      return TRUE;
    }

  }

  function getStatus($prop) {
    if($this->socket == null) {
      return FALSE;
    }
    
    if(in_array($prop, $this->props)) {
      $this->socket->write($this->appendNULL("STATUS " . $prop));

      $str = $this->socket->read();
      
      // format
      $str = trim($this->removeNULL($str));

      if($str == "ERROR") {
	$ret = $str;
      } else {
	$ret = substr($str, strlen("STATUS"), strlen($str));
      }
    } else {
      $ret = "PROPRIEDADE INVÁLIDA";
    }

    if($this->interactive) {
      printf("%s %s<br>", "Lendo $prop ...", "<b>$ret</b>");
    }

    return $ret;

  }

  function setStatus($prop, $value) {
    if($this->socket == null) {
      return FALSE;
    }

    if(in_array($prop, $this->props)) {
      $this->socket->write($this->appendNULL("SETSTATUS " . $prop . " " . ($value)));

      $str = $this->socket->read();
      $ret = trim($this->removeNULL($str));
    } else {
      $ret = "PROPRIEDADE INVÁLIDA";
    }

    if($this->interactive) {
      printf("%s %s<br>", "Setando $prop = <i>$value</i> ...", "<b>$ret</b>");
    }

    return $ret;

  }

  function notify($prop) {

    if($this->socket == null) {
      return FALSE;
    }

    if(in_array($prop, $this->props)) {

      $this->socket->write($this->appendNULL("NOTIFY " . $prop));

      $str = $this->socket->read();
      $ret = trim($this->removeNULL($str));

      // wait until notification arrive
      $read = array($this->socket);
      $num = socket_select($read, $write = NULL, $exp = NULL, NULL);    
 
     if($num) {
	$str = $this->socket->read();
	$ret = trim($this->removeNULL($str));
      }	

    } else {
      $ret = "PROPRIEDADE INVÁLIDA";
    }

    return $ret;

  }

  function isBusy() {
    if($this->socket == null) {
      return FALSE;
    }

    $ret = $this->getStatus($this->name);

    $cmp = trim($ret);

    if($cmp == "OFFLINE" || $cmp == "IDLE" || $cmp == "DISABLED")
      return FALSE;
    else
      return TRUE;

  }

  function appendNULL($str) {
    return $str . "\x00";
  }

  function removeNULL($str) {

    return substr($str, 0, strlen($str) -1);

  }

  function disconnect() {
    if($this->socket != null) {
      $this->socket->write($this->appendNULL("QUIT"));
      $this->socket->disconnect();
    }

  }

  function setInteractive($interactive) {
    $this->interactive = $interactive;
  }

}


class Sync extends Sec {

  function Sync($type = 'control') {
    
    $props = array(
		   "SYNC",
		   "EXPTIME",
		   "NEXP",
		   "BFNAME",
		   "INDEX",
		   "TELSTART",
		   "CAMSTART",
		   "OBSERVER",
		   "RA",
		   "DEC",
		   "EPOCH",
		   "FILTER",
		   "TASK");

    return parent::Sec("SYNC", $type, $props);

  }

}

class CCD extends Sec {

  function CCD($type = 'control') {
    
    $props = array(
		   "CCD",
		   "TASK",
		   "TYPE",
		   "CCD_TRIGGER",
		   "MOVING");


    $this->type = $type;

    return parent::Sec("CCD", $type, $props);

  }
  
}

class Tel extends Sec {

  function Tel($type = 'control') {
    
    $props = array(
		   "TEL",
		   "TASK",
		   "TYPE",
		   "CCD_TRIGGER",
		   "MOVING");

    return parent::Sec("TEL", $type, $props);

  }

}

?>