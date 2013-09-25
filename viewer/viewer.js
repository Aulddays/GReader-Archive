// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

var subscriptions = {};
var curFeed = '';
var curFeedIdx = null;
var curStart = 0;
var curEnd = 0;
var curData = [];
var curDataFile = '';
var page = 0, pagel = 50;
var curUser = '';
var isIE = false;

$(document).ready(function() {
	// detect IE
	if(navigator.appName == "Microsoft Internet Explorer"){
		isIE = true;
	}
	
	// viewer header buttons
	$( "#page-no" ).button();
	$( "#page-len" ).buttonset();
	$("input[name='page-len']").change(onSetPageLen);
	$( "#page-up" ).button({text: false, icons: {primary: "ui-icon-arrowthick-1-w"}});
	$( "#page-down" ).button({text: false, icons: {primary: "ui-icon-arrowthick-1-e"}});
	$( "#page-0" ).button({text: false, icons: {primary: "ui-icon-arrowthickstop-1-w"}});
	$( "#page-last" ).button({text: false, icons: {primary: "ui-icon-arrowthickstop-1-e"}});
	$( '.page-button' ).click(onSetPage);
	
	$('#scrollable-sections-holder').css('top',
		($('#logo-section').offset().top + $('#logo-section').height() + 5) + 'px');
	$('#viewer-container').css('top',
		($('#viewer-header-container').offset().top + $('#viewer-header-container').height() + 8) + 'px');
	//$( "#page-len" ).buttonset();
	//// Hover states for command icons
	//$( "#viewer-header div" ).hover(
	//	function() {
	//		$( this ).addClass( "ui-state-hover" );
	//	},
	//	function() {
	//		$( this ).removeClass( "ui-state-hover" );
	//	}
	//).mousedown(
	//	function() {
	//		$( this ).addClass( "ui-state-active" );
	//	}
	//).mouseup(
	//	function() {
	//		$( this ).removeClass( "ui-state-active" );
	//	}
	//);
	parseUrlParam();
	loadUsers();
});

function loadUsers()
{
	$.ajax({dataType: 'json', url: "./data/users.json"})
		.done(function(data) {
			$('.entry-tpl').hide();
			$('#entry-tpl1').show();
			var lastuser = '';
			var userno = 0;
			$('.user-selection').remove();
			var usertpl = $('.user-selection-sample');
			$.each(data, function(i, user){
				lastuser = user;
				++userno;
				var item = usertpl.clone().show();
				item.find("a").text(decodeURIComponent(user));
				item.find("a").attr('href', '#' + user);
				item.find("a").click(loadSubscription);
				usertpl.parent().append(item);
				if(curUser != '' && curUser == user)
				{
					$('#entry-tpl1').hide();
					loadSubscription();
					return false;	// break $each()
				}
			});	// $.each(subscriptions, function(i, sub){
			if(userno == 1)	// only one user, just show
			{
				curUser = lastuser;
				updateUrlParam();
				$('#entry-tpl1').hide();
				loadSubscription();
			}
		});
}

function loadSubscription(event) {
	if(event && $(this).attr('href') && $(this).attr('href').charAt(0) == '#')
	{
		curUser = $(this).attr('href').substring(1);
	}
	var subUrl = "./data/" + curUser + "/subscriptions_viewer.json"
	$.ajax({dataType: 'json', url: subUrl})
		.done(function(data) {
			subscriptions = data.subscriptions;
			var dirtpl = $('#sub-tree-item-dirsample-main');
			var itemtpl = $('#sub-tree-item-itemsample-main');
			var diritemtpl = $('#sub-tree-item-diritemsample-main');
			var lastdir = dirtpl;
			var node;
			dirtpl.hide();
			itemtpl.hide();
			diritemtpl.hide();
			var dirmap = {};
			$.each(subscriptions, function(i, sub){
				if (sub.categories && sub.categories.length > 0) {
					// console.log(sub.categories);
					$.each(sub.categories, function(j, cat){
						var dir;
						if (!dirmap[cat.label]) {
							// create directory
							var item = dirtpl.clone().show();
							item.attr('id', 'sub-tree-item-dir' + (dirmap.length + 1) + '-main');
							node = item.find('#sub-tree-item-dirsample-link');
							node.attr('id', 'sub-tree-item-dir' + (dirmap.length + 1) + '-link');
							node.attr('href', './label/' + cat.label);
							node.click(function(e){e.stopPropagation();return false;});
							node = item.find('#sub-tree-item-dirsample-name');
							node.attr('id', 'sub-tree-item-dir' + (dirmap.length + 1) + '-name');
							node.text(cat.label);
							node = item.find('#sub-tree-item-dirsample-action');
							node.attr('id', 'sub-tree-item-dir' + (dirmap.length + 1) + '-action');
							//dirtpl.parent().append(item);
							item.insertAfter(lastdir);
							lastdir = item;
							dirmap[cat.label] = item;
						}
						dir = dirmap[cat.label];
						var item = diritemtpl.clone().show();
						item.attr('id', 'sub-tree-item-' + (i + 1) + '_' + (j + 1) + '-main');
						node = item.find('#sub-tree-item-diritemsample-link');
						node.attr('id', 'sub-tree-item-' + (i + 1) + '_' + (j + 1) + '-link');
						node.attr('href', sub.id);
						node.click(onSwitchFeed);
						node = item.find('#sub-tree-item-diritemsample-name');
						node.attr('id', 'sub-tree-item-' + (i + 1) + '_' + (j + 1) + '-name');
						node.text(sub.title);
						node = item.find('#sub-tree-item-diritemsample-unread-count');
						node.attr('id', 'sub-tree-item-' + (i + 1) + '_' + (j + 1) + '-unread-count');
						if(typeof sub.GR_total === "undefined")
							sub.GR_total = 0;
						node.text('(' + sub.GR_total + ')');
						node = item.find('#sub-tree-item-diritemsample-action');
						node.attr('id', 'sub-tree-item-' + (i + 1) + '_' + (j + 1) + '-action');
						dir.find('#sub-tree-item-diritemsample-main').parent().append(item);
					});	// $.each(sub.categories, function(j, cat){
				}	// if (sub.categories && sub.categories.length > 0) {
				else {
					// regular item
					//$('#sub-tree-item-diritemsample-main').append($('#sub-tree-item-itemsample-main'));
					var item = itemtpl.clone().show();
					item.attr("id", 'sub-tree-item-' + (i + 1) + '-main');
					node = item.find('#sub-tree-item-itemsample-link');
					node.attr('id', 'sub-tree-item-' + (i + 1) + '-link');
					node.click(onSwitchFeed);
					node.attr('href', sub.id);
					node = item.find('#sub-tree-item-itemsample-name');
					node.attr('id', 'sub-tree-item-' + (i + 1) + '-name');
					node.text(sub.title);
					node = item.find('#sub-tree-item-itemsample-unread-count');
					node.attr('id', 'sub-tree-item-' + (i + 1) + '-unread-count');
					if(typeof sub.GR_total === "undefined")
						sub.GR_total = 0;
					node.text('(' + sub.GR_total + ')');
					node = item.find('#sub-tree-item-itemsample-action');
					node.attr('id', 'sub-tree-item-' + (i + 1) + '-action');
					itemtpl.parent().append(item);
				}
			});
			onSwitchFeed();
		})
		.fail(function() {
			console.log('loadSubscription fail');
			$('.entry-tpl').hide();
			$('#entry-tpl3').show();
		})
		.always(function() {
			//console.log('loadSubscription done');
		});
}

function onSwitchFeed(event) {
	var feedidx = null;
	if(event)
	{
		event.preventDefault();
		feedidx = /^sub-tree-item-(([0-9]+)(_[0-9]+)?)-link$/g.exec($(this).attr('id'));
		if(!feedidx)
		{
			alert("Opps, something was wrong...");
			return;
		}
		feedidx = feedidx[1];
	}
	if (curFeedIdx != feedidx) {
		if(feedidx == null)	// curFeedIdx!=null implied => event==null => not called by click but manually
		{
			feedidx = curFeedIdx;
			curFeedIdx = null;
		}
		if (curFeedIdx) {
			$('#sub-tree-item-' + curFeedIdx + '-link').removeClass('tree-link-selected');
			$('#sub-tree-item-' + curFeedIdx + '-name').removeClass('name-unread');
		}
		$('#sub-tree-item-' + feedidx + '-name').parent().addClass('tree-link-selected');
		$('#sub-tree-item-' + feedidx + '-name').addClass('name-unread');
		curFeedIdx = feedidx;
	}
	if(curFeedIdx)
	{
		updateUrlParam();
		showContent();
	}
	else
	{
		$('.entry-tpl').hide();
		$('#entry-tpl2').show();
	}
	return false;
}

function showContent() {
	parseUrlParam();
	// page, start, end is 0 based; feed and feedidx is 1 based; end is exluded
	var feed, start = 0, end = 0, dataFile, sub;
	$("#page-no").button( "option", "label", "Page 0 / 0" );
	if (curFeedIdx)
	{
		feed = parseInt(curFeedIdx.split('_')[0]);
		if (feed <= 0 || feed > subscriptions.length) {
			alert("Opps, something was wrong...");
			return;
		}
		sub = subscriptions[feed - 1];
		if(typeof sub.GR_total === "undefined" || typeof sub.GR_counts === "undefined" ||
			typeof sub.GR_dir === "undefined")
		{
			$('.entry-tpl').hide();
			$('#entry-tpl3').show();
			return;
		}
		maxpage = Math.floor((sub.GR_total - 1) / pagel);
		if(maxpage < 0)
			maxpage = 0;
		if(page < 0)
			page = 0;
		if(page > maxpage)
			page = maxpage;
		start = page * pagel;
		end = (page + 1) * pagel;
		if(end > sub.GR_total)
			end = sub.GR_total;
		window.location.href = '#' + curUser + '|' + curFeedIdx + '|' + pagel + '|' + page;
		$("#page-no").button( "option", "label", sprintf('Page %d / %d', page + 1, maxpage + 1) );
		$('#chrome-title-link').attr('href', sub.htmlUrl);
		$('#chrome-title-link').text(sub.title);
		$('#loading').show();
		$('.entry-show').remove();
		var cum = 0;	// no. of items in all previous xmls
		(function loadnShow(idx) {	// idx is xml index
			if(idx >= sub.GR_counts.length || start < cum)	// no (need to load) more xmls
			{
				$('#viewer-container').scrollTop(0)
				$('#loading').hide();
				return;
			}
			var num = sub.GR_counts[idx];
			if(start > cum + num)	// no needed item in current xml
			{
				cum += sub.GR_counts[idx];
				loadnShow(idx + 1);
				return;
			}
			(function loadFunc(showFunc){
				var dataFile = sprintf('./%s/%03d.xml', sub.GR_dir, idx);
				if(dataFile == curDataFile)	// already loaded
				{
					showFunc();
					return;
				}
				// load
				curData = [];
				var dataUrl = dataFile;
				// IE does not handle urlencoded chars in path (probably because IE handles local files as 'C:\data\file'
				// instead of 'file:///C:/data/file'). So decode first here for IE. On Windows, it seems that Firefox
				// and Chrome also accept decoded urls (haven't try other OSes),
				// but there stands chances that decoded data url is invalid, like file name containing '/', so still
				// pass encoded urls to non-IE browsers (in such cases IE will probably fail to load the data file
				// eventually)
				if(isIE)
					dataUrl = decodeURIComponent(dataFile);
				$.ajax({dataType: 'xml', url: dataUrl})
					.done(function(data) {
						var root = data.documentElement;
						$.each(root.getElementsByTagName("entry"), function(eidx, entry){
							var edata = {};
							edata.content = edata.base = edata.title = edata.link = edata.time = "";
							if($(entry).children("title")[0])
								edata.title = $(entry).children("title")[0].textContent;
							if(edata.title == '(title unknown)')
								console.log(curData.length + ' ' + edata.title);
							if($(entry).children("link")[0])
								edata.link = $(entry).children("link")[0].getAttribute('href');
							if($(entry).children("updated")[0])
								edata.time = $(entry).children("updated")[0].textContent;
							var contentnode = $(entry).children("content")[0];
							if(!contentnode)
								contentnode = $(entry).children("summary")[0];
							if(contentnode)
							{
								edata.content = contentnode.textContent;
								edata.base = contentnode.getAttribute('xml:base');
							}
							curData.push(edata);
						});
						curDataFile = dataFile;
						showFunc();
					})
					.fail(function() {
						console.log('loadFunc(' + dataFile + ') fail');
						$('#viewer-container').scrollTop(0)
						$('#loading').hide();
						$('.entry-tpl').hide();
						$('#entry-tpl3').show();
					});
			})(function showFunc(){	// call loadFunc() with parameter set to showFunc
				$('.entry-tpl').hide();
				var etpl = $('#entry-tpl0');
				for(var eidx = start - cum; eidx < Math.min(end - cum, num, curData.length); ++eidx)
				{
					var edata = curData[eidx];
					var entry = etpl.clone().show().removeAttr('id').addClass('entry-show');
					var node = entry.find('.entry-title-link');
					node.attr('href', edata.link);
					if(edata.link == '')
					{
						node.removeAttr('href');
						node.click(function(){return false;});
					}
					node.text(edata.title);
					var date = new Date(edata.time);
					entry.find('.entry-date').text(date.toLocaleDateString() + ' ' + date.toLocaleTimeString());
					// entry.find('.item-body').find('div').find('p').html(edata.content);
					entry.find('.item-div').html(edata.content);
					etpl.parent().append(entry);
				}
				cum += sub.GR_counts[idx];
				loadnShow(idx + 1);
			});
		})(0);
	}	// if (curFeedIdx)
}

function loadData(dir, idx) {
	var dataFile = sprintf('./%s/%03d.xml', dir, idx);
	if(dataFile == curDataFile)
		return true;
	curData = [];
	$.ajax({dataType: 'xml', url: dataFile})
		.done(function(data) {
			console.log('loadData ok');
		})
		.fail(function() {
			console.log('loadData(' + dataFile + ') fail');
		})
		.always(function() {
			console.log('loadData done');
		});

}

function parseUrlParam() {
	var url = window.location.href;
	var params = url.split('#')[1];
	curFeedIdx = null, page = 0, pagel = 50;
	var pagelidx = 2;
	if (params && params.length > 0)
	{
		// params: user|feedix|pagel|page
		params = params.split('|');
		$.each(params, function(i, val){
			if(i == 0)
				curUser = val;
			else if(i == 1)
				curFeedIdx = val;
			else if(i == 2)
				pagel = parseInt(val);
			else if(i == 3)
				page = parseInt(val);
			else
				return;
		});
		if (pagel <= 10)
		{
			pagel = 10; pagelidx = 0;
		}
		else if (pagel <= 20) 
		{
			pagel = 20; pagelidx = 1;
		}
		else if (pagel <= 50) 
		{
			pagel = 50; pagelidx = 2;
		}
		else
		{
			pagel = 100; pagelidx = 3;
		}
		if (page < 0)
			page = 0;
	}
	$('input:radio[name=page-len]')[pagelidx].checked = true;
	$( "#page-len" ).buttonset('refresh');
	updateUrlParam();
}

function updateUrlParam()
{
	if(curUser != '')
		$('#sub-tree-item-0-name').text(decodeURIComponent(curUser));
	if(curFeedIdx)
		window.location.href = '#' + curUser + '|' + curFeedIdx + '|' + pagel + '|' + page;
	else if(curUser)
		window.location.href = '#' + curUser;
}

function onSetPage(event) {
	event.preventDefault();
	var method = $(this).attr('id');
	if(method.lastIndexOf('page-', 0) !== 0)
		return;
	method = method.substring('page-'.length);
	switch (method) {
	case '0':
		page = 0;
		break;
	case 'up':
		page--;
		break;
	case 'down':
		page++;
		break;
	case 'last':
		page = 99999999;	// for convenience. should work for 99.9%+ cases
		break;
	default:	// invalid command
		return;	// do not refresh
	}
		window.location.href = '#' + curUser + '|' + curFeedIdx + '|' + pagel + '|' + page;
	showContent();
}

function onSetPageLen(event) {
	event.preventDefault();
	var newLen = $("input[name='page-len']:checked").attr('id');
	if(newLen.lastIndexOf('pagelen-', 0) !== 0)
		return;
	newLen = newLen.substring('pagelen-'.length);
	if(newLen != '10' && newLen != '20' && newLen != '50' && newLen != '100')
		return;
	newLen = parseInt(newLen);
	// compute new page so that the first item in current page will show under new pagel
	page = Math.floor(page * pagel / newLen);
	pagel = newLen;
		window.location.href = '#' + curUser + '|' + curFeedIdx + '|' + pagel + '|' + page;
	showContent();
}
