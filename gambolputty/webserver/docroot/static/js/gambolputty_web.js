$(document).ready(function()	{
	updateServerSystemInfo()
	setInterval(updateServerSystemInfo,5000);
	updateLogs()
})

function updateLogs() {
	// Select all log divs.
	$("div:regex(id, .*_log)").each(function(idx)	{
		// Extract hostname.
		var hostname = $(this).attr('id').replace('_log', '');
		var container = this
		var ws = new WebSocket('ws://' + hostname +":"+location.port+"/"+ globalSettings.getLogsUrl);
	    ws.onmessage = function(evt) {
	    	data = JSON.parse(evt.data);
	    	log_message = ansi_up.ansi_to_html(data.log_message);
	    	content = $(container).html() + log_message + "<br>"
	        $(container).html(content)
	    };
	   	//ws.onerror = function(evt) { console.log(evt) };
	})
}

function confirmRestartGambolPuttyService(hostname)	{
	bootbox.confirm("Really restart GambolPutty service on server "+hostname+"?", function(result) {
		if(result)	{
			restartGambolPuttyService(hostname)
		}
	}); 	
}

function restartGambolPuttyService(hostname)	{
	$.getJSON("http://"+hostname+":"+location.port+"/"+globalSettings.restartServiceUrl, function(jsonData) {
		console.log(jsonData)
	})
}

function updateServerSystemInfo()	{
	// Select all sysinfo divs.
	$("div:regex(id, .*_sysinfo)").each(function(idx)	{
		// Extract hostname.
		var hostname = $(this).attr('id').replace('_sysinfo', '');
		var container = this
		// Get info from server.
		$.getJSON("http://"+hostname+":"+location.port+"/"+globalSettings.serverInfoUrl, function(jsonData) {
			// Set CPU count.
			var selector = '#'+escapeSelector(hostname+"_cpus")
			$(selector).html("&nbsp;"+jsonData.cpu_count+"&nbsp;CPUs")
			// Set RAM size.
			var selector = '#'+escapeSelector(hostname+"_ram")
			$(selector).html("&nbsp;"+bytesToSize(jsonData.memory.total)+"&nbsp;total,&nbsp;"+bytesToSize(jsonData.memory.available)+"&nbsp;free")
			// Set system load.
			var selector = '#'+escapeSelector(hostname+"_load")
			$(selector).html("&nbsp;"+roundToFixed(jsonData.load[0], 2)+",&nbsp"+roundToFixed(jsonData.load[1], 2)+",&nbsp"+roundToFixed(jsonData.load[2], 2)+"&nbsp")
			// Set disk info.
			var selector = '#'+escapeSelector(hostname+"_hdds")
			// Clear container
			$(selector).html("")
			for(disk in jsonData.disk_usage)	{
				elements = $('<div/>').html('<h5><i class="fa fa-hdd-o pull-left"></i><span>'+disk+'&nbsp;, '+bytesToSize(jsonData.disk_usage[disk].total)+'&nbsp;total,'+bytesToSize(jsonData.disk_usage[disk].free)+'&nbsp;free'+'</span></h5>').contents();
				$(selector).append(elements)
				//console.log(roundToFixed(jsonData.disk_usage[disk].free, 0))
			}
			// Show sysinfo.
			if ($(container).hasClass('invisible'))	{
				$(container).hide().removeClass('invisible').fadeIn(500)			
			}
		})
	})
}

function showServerConfiguration() {
	// Gets server config from server.
}
