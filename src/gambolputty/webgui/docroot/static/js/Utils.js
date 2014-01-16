if (typeof Object.create === 'undefined') {
    Object.create = function (o) { 
        function F() {} 
        F.prototype = o; 
        return new F(); 
    };
}

// Avoid `console` errors in browsers that lack a console.
(function() {
    var method;
    var noop = function () {};
    var methods = [
        'assert', 'clear', 'count', 'debug', 'dir', 'dirxml', 'error',
        'exception', 'group', 'groupCollapsed', 'groupEnd', 'info', 'log',
        'markTimeline', 'profile', 'profileEnd', 'table', 'time', 'timeEnd',
        'timeStamp', 'trace', 'warn'
    ];
    var length = methods.length;
    var console = (window.console = window.console || {});

    while (length--) {
        method = methods[length];

        // Disable console completely if defined else only undefined methods.
        if (globalSettings.disableConsole || !console[method]) {
            console[method] = noop;
        }
    }
}());

/**
 * Add regex enabled selector.
 */
jQuery.expr[':'].regex = function(elem, index, match) {
    var matchParams = match[3].split(','),
        validLabels = /^(data|css):/,
        attr = {
            method: matchParams[0].match(validLabels) ?
                        matchParams[0].split(':')[0] : 'attr',
            property: matchParams.shift().replace(validLabels,'')
        },
        regexFlags = 'ig',
        regex = new RegExp(matchParams.join('').replace(/^\s+|\s+$/g,''), regexFlags);
    return regex.test(jQuery(elem)[attr.method](attr.property));
}

/**
 * Simple hash method for strings
 */
String.prototype.hashCode = function(){
	var hash = 0;
	if (this.length == 0) return hash;
	for (i = 0; i < this.length; i++) {
		char = this.charCodeAt(i);
		hash = ((hash<<5)-hash)+char;
		hash = hash & hash; // Convert to 32bit integer
	}
	return hash;
}

/**
 * Get date in local format
 * 
 * @param Object date object
 * @param string long || short format
 */
function getLocalDateTime(dateObject, format)	{
	return dateObject.f(i18n.t(format))
}

/**
 * Get fqdn from url
 * 
 * @param string
 * @return string
 */
function getFqdn(url) {
    var fqdn = url.match(/^https?:\/\/([^/]+)/);
    return fqdn ? fqdn[1] : null;
}

/** 
 * Get base URL
 * 
 * Returns the protocol + fqdn from the current url.
 * E.g.: URL: http://www.test.com/where/when
 * Return: http://www.test.com
 */
function getYiiBaseUrl()	{
	return yiiBaseUrl;
}

/**
 * Get hostname 
 * 
 * Either from URL or, if set, from parameter.
 */
function getHostName() {
	var hostName = stripTags(decodeURIComponent(getFqdn(document.URL)))
	if(hostNameParam = $.getUrlVar('Host'))
		hostName = hostNameParam
	return hostName
}

/**
 * Get current time as unix timestamp
 * 
 * @return unix timestamp
 */
function unixTime()	{
	return Math.round((new Date()).getTime() / 1000);
}

/**
 * Remove html tags from a string
 * 
 * @param string
 * @return string
 */
function stripTags(text) { 
	return text.replace(/<\/?[^>]+>/gi, '')
}

/**
 * Escape selector.
 * 
 * Escape problematic chars in a selector (e.g. dots)
 * 
 * @param string
 * @return string
 */
function escapeSelector(selector) {
	return selector.replace(/([ #;?%&,.+*~\':"!^$[\]()=>|\/@])/g,'\\$1')
}

/**
 * Convert number of bytes into human readable format
 *
 * @param integer bytes     Number of bytes to convert
 * @return string
 */
function bytesToSize(bytes) {
    var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return 'n/a';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[[i]];
};

/**
 * Round to a fixed number of decimal digits.
 * 
 * @param float
 * @param integer
 * @return float
 */
function roundToFixed(value, precision) {
    var precision = precision || 0,
    neg = value < 0,
    power = Math.pow(10, precision),
    value = Math.round(value * power),
    integral = String((neg ? Math.ceil : Math.floor)(value / power)),
    fraction = String((neg ? -value : value) % power),
    padding = new Array(Math.max(precision - fraction.length, 0) + 1).join('0');

    return precision ? integral + '.' +  padding + fraction : integral;
}