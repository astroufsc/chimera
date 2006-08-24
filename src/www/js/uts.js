<!--

var cleanExit = false;

function go() {

	cleanExit = true;

}


function logout() {

	window.open("logout.php?autoclose=1", width=100, height=100, status=0,
		    toolbar=0, location=0, menubar=0);

}


function checkCleanExit() {

	if(!cleanExit) {
	
		logout();
		
	}
}


function hideDiv(pass) {
  var divs = document.getElementsByTagName('div');
  for(i=0;i<divs.length;i++){
    if(divs[i].id.match(pass)){//if they are 'see' divs
      if (document.getElementById) // DOM3 = IE5, NS6
	divs[i].style.visibility="hidden";// show/hide
      else if (document.layers) // Netscape 4
	  document.layers[divs[i]].display = 'hidden';
      else // IE 4
	document.all.hideshow.divs[i].visibility = 'hidden';
    }
  }
}

function showDiv(pass) {
  var divs = document.getElementsByTagName('div');
  for(i=0;i<divs.length;i++){
    if(divs[i].id.match(pass)){
      if (document.getElementById)
	divs[i].style.visibility="visible";
      else if (document.layers) // Netscape 4
	document.layers[divs[i]].display = 'visible';
      else // IE 4
	document.all.hideshow.divs[i].visibility = 'visible';
    }
  }
}

function showMessage(txt) {

  alert(txt);

}


function confirma(msg) {

        if(confirm(msg)) {
                return true;
        } else {
                return false;
        }
}

function jsVal_Language() {

	this.err_enter = "Lah lah lah "%FIELDNAME%"";
	this.err_form = "Os seguintes campos devem ser preenchidos:\n\n";
	this.err_select = "Você deve selecionar um valor em "%FIELDNAME%"";

}

// -->