$(function() {
	$('a[href="#signup"]').click(function() {
		$(".view-signup").css("display", "block");
		$(".view-signin").css("display", "none");
		$('a[href="#signup"]').addClass("active");
		$('a[href="#signin"]').removeClass("active");
	});

	$('a[href="#signin"]').click(function() {
		$(".view-signup").css("display", "none");
		$(".view-signin").css("display", "block");
		$('a[href="#signin"]').addClass("active");
		$('a[href="#signup"]').removeClass("active");
	});
});

$('a[href="#signup"]').click(function() {
	$("div.navs-slider").attr("data-active-index", 0);
});
$('a[href="#signin"]').click(function() {
	$("div.navs-slider").attr("data-active-index", 1);
});

$('a[href="#signup"]').click(function() {
	window.location.hash = "#signup"
});

$('a[href="#signin"]').click(function() {
	window.location.hash = "#signin"
});