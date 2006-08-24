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

class Socket {
    
    var $fp = NULL;
    var $addr;
    var $port;

    function Socket() {
    }

    function connect($addr = 'localhost', $port) {
        if ($this->fp) {
	  socket_shutdown($this->fp, 2);
	  socket_close($this->fp);
	  $this->fp = NULL;
        }
        
        if (strspn($addr, '.0123456789') == strlen($addr)) {
            $this->addr = $addr;
        } else {
            $this->addr = gethostbyname($addr);
        }

        $this->port = $port;

	$this->fp = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if (!$this->fp) {
	  return FALSE;
        }

	if(!socket_connect($this->fp, $this->addr, $this->port)) {
	  return FALSE;
	}
        
        return TRUE;
    }

    function disconnect() {
        if($this->fp) {
	  socket_shutdown($this->fp, 2);
	  socket_close($this->fp);
	  $this->fp = NULL;
	  return TRUE;
        }

        return FALSE;
    }

    function read($size = 1024) {
        if ($this->fp) {
	  return socket_read($this->fp, $size);
        }

        return FALSE;
    }

    function write($data) {
        if ($this->fp) {
	  return socket_write($this->fp, $data, strlen($data));
	  // $ret = socket_write($this->fp, $data, strlen($data));
	  // echo "$ret<br>";
	  // return $ret;
        }
	
	return FALSE;
    }

}
?>
