
var myCountdown = new Array();
var repeat = false;

function checkPlural(noun, value) {
  noun = ((value == 1) || (value == 0)) ? noun : (noun += "s");
  return noun;
}

function updateDisplay(text, id) {
  var tag = document.getElementById(id);
  if (tag.firstChild) {
    tag.firstChild.nodeValue = text;
  }
  else {
    textNode = document.createTextNode(text);
    tag.appendChild(textNode);
  }
  return;
}

function doCountdown() {
  for (i = 0; i < myCountdown.length; i++) {
    if (!myCountdown[i].expired) {
      var currentDate = new Date();
      var eventDate = myCountdown[i].eventDate;
      var timeLeft = new Date();
      timeLeft = eventDate - currentDate;
      msPerDay = 24 * 60 * 60 * 1000;
      msPerHour = 60 * 60 * 1000;
      msPerMin = 60 * 1000;
      msPerSec = 1000;
      daysLeft = Math.floor(timeLeft / msPerDay);
      hoursLeft = Math.floor((timeLeft % msPerDay) / msPerHour);
      minsLeft = Math.floor(((timeLeft % msPerDay) % msPerHour) / msPerMin);
      secsLeft = Math.floor((((timeLeft % msPerDay) % msPerHour) % msPerMin) / msPerSec);
      hour = checkPlural("hora", hoursLeft);
      minute = checkPlural("minuto", minsLeft);
      second = checkPlural("segundo", secsLeft);
      if ((daysLeft == 0) && (hoursLeft == 0) && (minsLeft == 0) && (secsLeft == 0)) {
        updateDisplay(myCountdown[i].onevent, myCountdown[i].tagID);
      }
      else {
        if (daysLeft <= -1) {
          updateDisplay(myCountdown[i].afterevent, myCountdown[i].tagID);
          myCountdown[i].expired = true;
        }
        else {
          updateDisplay(hoursLeft + ":" + minsLeft + ":" + secsLeft, myCountdown[i].tagID);
          repeat = true;
        }
      }
    }
  }
  if (repeat) {
    repeat = false;
    window.setTimeout("doCountdown()", 1000);
  }
  else {
    return;
  }
}

function setEventDate(year, month, day, hour, minute, second) {
//function setEventDate(second) {
  this.eventDate = new Date(year, month - 1, day, hour, minute, second);
  return;
}

function addCountdown(countdown) {
  myCountdown[myCountdown.length] = countdown;
  return;
}

function Countdown() {
  this.tagID = "";
  this.eventDate = new Date();
  this.setEventDate = setEventDate;
  this.event = "";
  this.onevent = "";
  this.afterevent = "";
  this.expired = false;
}