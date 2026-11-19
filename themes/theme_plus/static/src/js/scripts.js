/* Template: Plus - StartUp HTML Landing Page Template
   Author: Inovatik
   Created: June 2019
   Description: Custom JS file
   */


   (function($) {
    "use strict"; 

    /* Preloader */
    $(window).on('load', function() {
      var preloaderFadeOutTime = 500;
      function hidePreloader() {
         var preloader = $('.spinner-wrapper');
         setTimeout(function() {
            preloader.fadeOut(preloaderFadeOutTime);
        }, 500);
     }
     hidePreloader();
 });


    /* Navbar Scripts */
/*    $(window).on('scroll load', function() {
    	console.log("=================")
      if ($(".navbar").offset().top > 60) {
         $(".fixed-top").addClass("top-nav-collapse");
     } else {
         $(".fixed-top").removeClass("top-nav-collapse");
     }
 });*/

    $(window).on('scroll',function(){  
        if ($(window).scrollTop() > 60) {
          $('.fixed-top').addClass("top-nav-collapse");
      }
      else{
          $('.fixed-top').removeClass("top-nav-collapse");
      }   
  });

	/*$(function() {
		$(document).on('click', 'a.page-scroll', function(event) {
			var $anchor = $(this);
			$('html, body').stop().animate({
				scrollTop: $($anchor.attr('href')).offset().top
			}, 600, 'easeInOutExpo');
			event.preventDefault();
		});
	});*/
//
//    $("#header_nav .navbar-nav li a").on("click", function(event) {
//    if (!$(this).parent().hasClass('dropdown'))
//        $(".navbar-collapse").collapse('hide');
//    });


/* Image Slider - Swiper */
var imageSlider = new Swiper('.image-slider', {
    autoplay: {
        delay: 2000,
        disableOnInteraction: false
    },
    loop: true,
    spaceBetween: 30,
    slidesPerView: 5,
    breakpoints: {
        580: {
            slidesPerView: 1,
            spaceBetween: 10
        },
        768: {
            slidesPerView: 2,
            spaceBetween: 20
        },
        992: {
            slidesPerView: 3,
            spaceBetween: 20
        },
        1200: {
            slidesPerView: 4,
            spaceBetween: 20
        },

    }
});


/* Card Slider - Swiper */
var cardSlider = new Swiper('.card-slider', {
  autoplay: {
    delay: 4000,
    disableOnInteraction: false
},
loop: true,
navigation: {
 nextEl: '.swiper-button-next',
 prevEl: '.swiper-button-prev'
}
});


/* Video Lightbox - Magnific Popup */
$('.popup-youtube, .popup-vimeo').magnificPopup({
    disableOn: 700,
    type: 'iframe',
    mainClass: 'mfp-fade',
    removalDelay: 160,
    preloader: false,
    fixedContentPos: false,
    iframe: {
        patterns: {
            youtube: {
                index: 'youtube.com/', 
                id: function(url) {        
                    var m = url.match(/[\\?\\&]v=([^\\?\\&]+)/);
                    if ( !m || !m[1] ) return null;
                    return m[1];
                },
                src: 'https://www.youtube.com/embed/%id%?autoplay=1'
            },
            vimeo: {
                index: 'vimeo.com/', 
                id: function(url) {        
                    var m = url.match(/(https?:\/\/)?(www.)?(player.)?vimeo.com\/([a-z]*\/)*([0-9]{6,11})[?]?.*/);
                    if ( !m || !m[5] ) return null;
                    return m[5];
                },
                src: 'https://player.vimeo.com/video/%id%?autoplay=1'
            }
        }
    }
});


/* Lightbox - Magnific Popup */
$('.popup-with-move-anim').magnificPopup({
  type: 'inline',
  fixedContentPos: false, /* keep it false to avoid html tag shift with margin-right: 17px */
  fixedBgPos: true,
  overflowY: 'auto',
  closeBtnInside: true,
  preloader: false,
  midClick: true,
  removalDelay: 300,
  mainClass: 'my-mfp-slide-bottom'
});


/* Move Form Fields Label When User Types */
$("input, textarea").keyup(function(){
  if ($(this).val() != '') {
     $(this).addClass('notEmpty');
 } else {
     $(this).removeClass('notEmpty');
 }
});


/* Request Form */
$("#requestForm").validator().on("submit", function(event) {
   if (event.isDefaultPrevented()) {
    rformError();
    rsubmitMSG(false, "Please fill all fields!");
} else {
    event.preventDefault();
    rsubmitForm();
}
});

function rsubmitForm() {
  var name = $("#rname").val();
  var email = $("#remail").val();
  var phone = $("#rphone").val();
  var select = $("#rselect").val();
  var terms = $("#rterms").val();

  $.ajax({
    type: "POST",
    url: "php/requestform-process.php",
    data: "name=" + name + "&email=" + email + "&phone=" + phone + "&select=" + select + "&terms=" + terms, 
    success: function(text) {
        if (text == "success") {
            rformSuccess();
        } else {
            rformError();
            rsubmitMSG(false, text);
        }
    }
});
}

function rformSuccess() {
    $("#requestForm")[0].reset();
    rsubmitMSG(true, "Request Submitted!");
    $("input").removeClass('notEmpty'); 
}

function rformError() {
    $("#requestForm").removeClass().addClass('shake animated').one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
        $(this).removeClass();
    });
}

function rsubmitMSG(valid, msg) {
    if (valid) {
        var msgClasses = "h3 text-center tada animated";
    } else {
        var msgClasses = "h3 text-center";
    }
    $("#rmsgSubmit").removeClass().addClass(msgClasses).text(msg);
}


/* Contact Form */
$("#contactForm").validator().on("submit", function(event) {
   console.log("method called form C");
   if (event.isDefaultPrevented()) {
    cformError();
    csubmitMSG(false, "Please fill all fields!");
} else {
    event.preventDefault();
    csubmitForm();
}
}); 

function csubmitForm() {
  var name = $("#cname").val();
  var email = $("#cemail").val();
  var message = $("#cmessage").val();
  var subject = $("#csubject").val();
  $.ajax({
    type: "POST",
            url: "/contact_form/", //"php/contactform-process.php",
            data: "name=" + name + "&email=" + email + "&message=" + message + "&subject=" + subject, 
            success: function(text) {
                if (text == "success") {
                    cformSuccess();
                } else {
                    cformError();
                    csubmitMSG(false, text);
                }
            }
        });
}

function cformSuccess() {
    $("#contactForm")[0].reset();
    csubmitMSG(true, "Message Submitted!");
    $("input").removeClass('notEmpty'); 
    $("textarea").removeClass('notEmpty'); 
}

function cformError() {
    $("#contactForm").removeClass().addClass('shake animated').one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
        $(this).removeClass();
    });
}

function csubmitMSG(valid, msg) {
    if (valid) {
        var msgClasses = "h3 text-center tada animated";
    } else {
        var msgClasses = "h3 text-center";
    }
    $("#cmsgSubmit").removeClass().addClass(msgClasses).text(msg);
}

/*
    $("#privacyForm").validator().on("submit", function(event) {
    	if (event.isDefaultPrevented()) {
            
            pformError();
            psubmitMSG(false, "Please fill all fields!");
        } else {
            
            event.preventDefault();
            psubmitForm();
        }
    });

    function psubmitForm() {
        
		var name = $("#pname").val();
		var email = $("#pemail").val();
        var select = $("#pselect").val();
        var terms = $("#pterms").val();
        
        $.ajax({
            type: "POST",
            url: "php/privacyform-process.php",
            data: "name=" + name + "&email=" + email + "&select=" + select + "&terms=" + terms, 
            success: function(text) {
                if (text == "success") {
                    pformSuccess();
                } else {
                    pformError();
                    psubmitMSG(false, text);
                }
            }
        });
	}

    function pformSuccess() {
        $("#privacyForm")[0].reset();
        psubmitMSG(true, "Request Submitted!");
        $("input").removeClass('notEmpty'); 
    }

    function pformError() {
        $("#privacyForm").removeClass().addClass('shake animated').one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
            $(this).removeClass();
        });
	}

    function psubmitMSG(valid, msg) {
        if (valid) {
            var msgClasses = "h3 text-center tada animated";
        } else {
            var msgClasses = "h3 text-center";
        }
        $("#pmsgSubmit").removeClass().addClass(msgClasses).text(msg);
    }
    
    */ 
    
//    /* Back To Top Button */
//    $('body').prepend('<a href="body" class="back-to-top page-scroll">Back to Top</a>');
//    var amountScrolled = 700;
//    $(window).scroll(function() {
//        if ($(window).scrollTop() > amountScrolled) {
//            $('a.back-to-top').fadeIn('500');
//        } else {
//            $('a.back-to-top').fadeOut('500');
//        }
//    });



/* Removes Long Focus On Buttons */
$(".button, a, button").mouseup(function() {
  $(this).blur();
});



	/*function scrollNav() {
        $('.navbar-nav .nav-item a').click(function(){  
          $(".active").removeClass("active");      
          $(this).closest('a').addClass("active");
          var theClass = $(this).attr("class");
          $('.'+theClass).parent('a').addClass('active');
          console.log("active");
          $('html, body').stop().animate({
              scrollTop: $( $(this).attr('href') ).offset().top
          }, 400);
          console.log("scroll");
          return false;
        });
        $('.scrollTop a').scrollTop();
      }
      scrollNav();
      */

//	function scrollNav() {
//	$("#header_nav .navbar-nav .nav-item a").on('click',function(e) {
//        var url = e.target.href;
//        var hash = url.substring(url.indexOf("#")+1);
//        $(".active").removeClass("active");      
//        $(this).closest('a').addClass("active");
//        var theClass = $(this).attr("class");
//        $('.'+theClass).parent('a').addClass('active');
//        $('html, body').animate({
//            scrollTop: $('#'+hash).offset().top - $('.navbar').outerHeight(),
//        }, 500);
//        return false;
//    });
//	$('.scrollTop a').scrollTop();
//    }
//    scrollNav();

})(jQuery);

