$(document).ready(function() {
    $(".has-tooltip").tooltip();
});

/* Enable smooth scrolling on all links with anchors */
$('#nav ul li a[href^="#"]').on('click', function(e) {

  // prevent default anchor click behavior
  e.preventDefault();

  // store hash
  var hash = this.hash;

  // animate
  $('html, body').animate({
    scrollTop: $('a[name="' + this.hash.replace('#', '') + '"]').offset().top
  }, 300, function(){

    // when done, add hash to url
    // (default click behaviour)
    window.location.hash = hash;

  });
});

