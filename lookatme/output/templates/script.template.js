/* REMOVE ME: (all lines with "REMOVE ME" will be removed by the templating code)
 * REMOVE ME: This template CSS uses a basic jinja templating syntax:
 * REMOVE ME:
 * REMOVE ME: \{\{VARIABLE\}\}
   REMOVE ME: */

var SLIDES = {};
var NAV_BY_SLIDE = {};
var CURR_SLIDE = 0;

function onload() {
  let navSlideItems = document.getElementsByClassName("navitem-slide");
  Array.prototype.forEach.call(navSlideItems, function(elem) {
    elem.addEventListener("click", onNavClick, false);
    let slideIdx = parseInt(elem.dataset.slideIdx);
    NAV_BY_SLIDE[slideIdx] = elem;
  });

  let slideItems = document.getElementsByClassName("slide");
  Array.prototype.forEach.call(slideItems, function(elem) {
    let slideIdx = parseInt(elem.dataset.slideIdx);
    SLIDES[slideIdx] = elem;
    elem.classList.add("hidden");
    injectScrollbar(elem);
  });

  window.addEventListener("resize", () => {
    for (let slideIdx of Object.keys(SLIDES)) {
      let slide = SLIDES[slideIdx];
      slide.scrollbar.update();
    }
  });

  document.addEventListener("keydown", onKeypress);
  setSlideIdx(CURR_SLIDE);
}

function enterFullScreen(element) {
  if(element.requestFullscreen) {
    element.requestFullscreen();
  } else if (element.msRequestFullscreen) {
    element.msRequestFullscreen();
  } else if (element.mozRequestFullScreen) {
    element.mozRequestFullScreen();
  } else if (element.webkitRequestFullscreen) {
    element.webkitRequestFullscreen();
  }
}

function exitFullscreen() {
  if(document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.mozCancelFullScreen) {
    document.mozCancelFullScreen();
  } else if (document.webkitExitFullscreen) {
    document.webkitExitFullscreen();
  }
}

function onNavClick(e) {
  let item = e.currentTarget;
  let slideIdx = parseInt(item.dataset.slideIdx);
  setSlideIdx(slideIdx);
}

function setSlideIdx(idx) {
  getSlide().classList.add("hidden");
  let navElem = getNav();
  if (navElem) {
    navElem.classList.remove("nav-active");
  }

  CURR_SLIDE = idx;

  let slideElem = getSlide();
  slideElem.classList.remove("hidden");
  slideElem.querySelector(".slide-body-inner").click();
  slideElem.querySelector(".slide-body-inner").focus();
  slideElem.scrollbar.update();

  navElem = getNav();
  if (navElem) {
    navElem.classList.add("nav-active");
  }
}

function setSlideIdxRel(amount) {
  let newIdx = CURR_SLIDE + amount;
  if (SLIDES[newIdx] === undefined) {
    return;
  }

  setSlideIdx(newIdx);
}

function getSlide() {
  return SLIDES[CURR_SLIDE];
}

function getNav() {
  var idx = CURR_SLIDE;
  while (idx >= 0 && !NAV_BY_SLIDE[idx]) {
    idx--;
  }
  return NAV_BY_SLIDE[idx];
}

const KEYS = {
  ARROW_UP: 38,
  ARROW_DOWN: 40,
  ARROW_LEFT: 41,
  ARROW_RIGHT: 39,
};

function onKeypress(_e) {
  let e = _e || window.event;
  let key = (e.key || String.fromCharCode(e.keyCode)).toLowerCase();

  if (e.shiftKey || e.controlKey || e.altKey) {
    return false;
  }

  switch (key) {
    case "arrowup":
      break;
    case "arrowdown":
      break;
    case "arrowleft":
    case "h":
    case "k":
      setSlideIdxRel(-1);
      break;
    case "arrowright":
    case "l":
    case "j":
      setSlideIdxRel(1);
      break;
  }
}

function getLineHeight(elem) {
  let singleLineSpan = document.createElement("div");
  singleLineSpan.innerHTML = "A";

  elem.appendChild(singleLineSpan);
  let computed = getComputedStyle(singleLineSpan);
  let height = parseFloat(computed.height);
  elem.removeChild(singleLineSpan);
  if (isNaN(height)) {
    return 0;
  }
  return height;
}

function needsScrollbar(elem) {
  return !(
    elem.scrollTop == 0
    && Math.abs(elem.scrollHeight - elem.clientHeight) < 1
  );
}

class Scrollbar {
  constructor(viewElem, watchElem) {
    this.viewElem = viewElem;
    this.watchElem = watchElem;

    this.gutter = document.createElement("div");
    this.gutter.classList.add("scrollbar-gutter");
    this.viewElem.addEventListener("scroll", () => this.update());

    this.slider = document.createElement("div");
    this.slider.classList.add("scrollbar-slider");

    // this shouldn't change...
    this.lineHeight = getLineHeight(this.watchElem);

    this.sliderTopChars = {{styles.scrollbar.slider.top_chars|json}};
    this.sliderFill = {{styles.scrollbar.slider.fill|json}};
    this.sliderBottomChars = {{styles.scrollbar.slider.bottom_chars|json}};

    this.gutterFill = {{styles.scrollbar.gutter.fill|json}};

    this.update();
  }

  appendTo(elem) {
    elem.appendChild(this.gutter);
  }

  update() {
    if (this.lineHeight == 0) {
      this.lineHeight = getLineHeight(this.watchElem);
    }
    if (this.lineHeight == 0) {
      return;
    }

    if (!needsScrollbar(this.viewElem)) {
      this.gutter.style.display = "none";
      return;
    }

    this.gutter.style.display = "block";

    let styles = getComputedStyle(this.watchElem);
    this.gutter.style.left = parseFloat(styles.width) + 2.0 + "px";

    let beforePx = this.viewElem.scrollTop;
    let visiblePx = this.viewElem.clientHeight;
    let afterPx = this.watchElem.scrollHeight - beforePx - visiblePx;
    let totalPx = this.watchElem.scrollHeight;

    let before = beforePx / this.lineHeight;
    let visible = visiblePx / this.lineHeight;
    let after = afterPx / this.lineHeight;
    let total = totalPx / this.lineHeight;

    let scrollPercent = before / (before + after);

    let sliderHeight = Math.max(visible * (visible / total), 2.0);
    let fillCount = sliderHeight;

    let sliderEndIdxF = sliderHeight + (visible - sliderHeight) * scrollPercent;
    let sliderEndVal = sliderEndIdxF - Math.floor(sliderEndIdxF);
    let sliderEndChar = "";
    if (sliderEndVal > 0.0) {
      fillCount -= sliderEndVal;
      sliderEndChar = this.sliderBottomChars[
        Math.floor(sliderEndVal / (1.0 / this.sliderBottomChars.length))
      ];
    }

    let sliderStartIdxF = sliderEndIdxF - sliderHeight;
    let sliderStartVal = 1.0 - (sliderStartIdxF - Math.floor(sliderStartIdxF));
    let sliderStartChar = "";
    if (sliderStartVal < 1.0) {
      fillCount -= sliderStartVal;
      sliderStartChar = this.sliderTopChars[
        Math.floor(sliderStartVal / (1.0 / this.sliderTopChars.length))
      ];
    }

    let sliderStartIdx = Math.floor(sliderStartIdxF);
    let sliderEndIdx = Math.ceil(sliderEndIdxF);

    let sliderChars = "";
    sliderChars += sliderStartChar;
    sliderChars += this.sliderFill.repeat(Math.round(fillCount));
    sliderChars += sliderEndChar;

    let gutterContent = this.gutterFill.repeat(visible + 1).split("").join("<br/>");
    this.gutter.innerHTML = gutterContent;

    this.gutter.appendChild(this.slider);
    this.slider.innerHTML = sliderChars.split("").join("<br/>");
    this.slider.style.top = "" + (sliderStartIdx * this.lineHeight) + "px";
  }
}

function injectScrollbar(slideElem) {
  let innerElem = slideElem.querySelector(".slide-body-inner");
  let innerInnerElem = slideElem.querySelector(".slide-body-inner-inner");
  let scrollbar = new Scrollbar(innerElem, innerInnerElem);
  scrollbar.appendTo(slideElem.querySelector(".slide-body"));
  slideElem.scrollbar = scrollbar;
}
