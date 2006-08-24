<?php

function jd($timestamp) {

	$d = getdate($timestamp);

	$jd  = 367 * $d['year'] - (7 * ($d['year'] + (($d['mon'] + 9)/12))/4);
	$jd += (275 * $d['mon']/9) + $d['mday'] + 1721013.5 + date("O", $timestamp)/24;

	return $jd;

}

function mjd($timestamp) {

	return jd($timestamp) - 2400000.5;

}

?>