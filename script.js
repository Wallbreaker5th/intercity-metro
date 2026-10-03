const AttributeBinding = {
  data() {
    return {
      lines: [],
    };
  },
  methods: {
    updateLines(lines) {
      this.lines = lines;
    },
  },
};

const app = Vue.createApp(AttributeBinding);

app.component("metro-line", {
  props: ["start", "end", "line", "color"],
  template: `<div class="metro-line">
    <div style="display:inline-block">
      <div class="station station-start">
      <span v-if="line.start.length<=8">{{line.start}}</span>
      <span v-if="line.start.length>8"><small>{{line.start}}</small></span>
      </div>
      <span v-bind:style="'color:'+line.color">-----------</span>
    </div>
    <div v-bind:style="'color:'+line.color+';display:inline-block;'">
        <span class="line" v-bind:style="'background-color:'+line.color">{{line.line}}</span>
    </div>
    <div style="display:inline-block">
      <span v-bind:style="'color:'+line.color">----------▶</span>
      <div class="station station-end">
      <span v-if="line.end.length<=8">{{line.end}}</span>
      <span v-if="line.end.length>8"><small>{{line.end}}</small></span
      </div>
    </div>
</div>`,
});

vm = app.mount("#lines-list");

var lines;
const stations = new Set();
const station2line = new Map();
const virtual_links = new Map();

const VIRTUAL_LINKS_KEY = "virtual_links";

function load_json() {
  const url = "metro.json";
  const request = new XMLHttpRequest();
  request.open("get", url);
  request.send(null);
  request.onload = function () {
    if (request.status == 200) {
      lines = JSON.parse(request.responseText);
    }
    if (VIRTUAL_LINKS_KEY in lines) {
      for (const pair of lines[VIRTUAL_LINKS_KEY]) {
        virtual_links.set(pair[0], pair[1]);
        virtual_links.set(pair[1], pair[0]);
      }
      delete lines[VIRTUAL_LINKS_KEY];
    }
    lines["成都"]["地铁1号线"]["stations"]["阿蒙森—斯科特"] = {};
    for (const city in lines) {
      for (const line in lines[city]) {
        for (const station in lines[city][line]["stations"]) {
          stations.add(station);
          if (!station2line.has(station)) {
            station2line.set(station, []);
          }
          station2line.get(station).push({city, line});
        }
      }
    }
    let options = "";
    for (const station of stations)
      options += '<option value="' + station + '" />';
    document.getElementById("stations").innerHTML = options;
  };
}

load_json();

function generatePathStep(line, start, end) {
  function getStationName(station) {
    let stationInfo = lines[line.city][line.line]["stations"][station];
    let name = station;
    if (stationInfo && stationInfo.displayName)
      name = stationInfo.displayName;
    return name + "站";

  }
  return {
    start: getStationName(start),
    end: getStationName(end),
    line: line.city + line.line,
    color: "#" + lines[line.city][line.line]["color"],
  };
}

function getpath(beg, end) {
  if (!(stations.has(beg) && stations.has(end))) return [];
  const queue = [];
  const expanded = new Set();
  let searchResult = null;

  queue.push({
    station: beg,
    from: null,
    distance: 0,
  });
  expanded.add(beg);

  while (queue.length > 0) {
    const front = queue.shift();
    if (front.station === end) {
      searchResult = front;
      break;
    }
    const currentStations = [front.station];
    if (virtual_links.has(front.station)) {
      currentStations.push(virtual_links.get(front.station));
    }
    for (const currentStation of currentStations) {
      for (const line of station2line.get(currentStation)) {
        for (const station in lines[line.city][line.line]["stations"]) {
          if (!expanded.has(station)) {
            expanded.add(station);
            queue.push({
              station: station,
              from: {
                previous: front,
                station: currentStation,
                line: line,
              },
              distance: front.distance + 1,
            });
          }
        }
      }
    }
  }

  if (!searchResult) {
    return [];
  }

  const path = [];
  let currentStation = searchResult;
  while (currentStation.from) {
    path.push(generatePathStep(currentStation.from.line, currentStation.from.station, currentStation.station));
    currentStation = currentStation.from.previous;
  }

  path.reverse();
  return path;
}

function updateLines() {
  var start=document.getElementById("start").value;
  var end=document.getElementById("end").value;
  var message=document.getElementById("message");
  vm.updateLines([]);
  if(!stations.has(start)){
    message.innerText="未知的起点站！";
    return;
  }
  if(!stations.has(end)){
    message.innerText="未知的终点站！";
    return;
  }
  var res=getpath(start,end);
  vm.updateLines(res);
  if(res.length==0){
    message.innerText="没有找到合适的路线……";
    return;
  }
  message.innerText="";
}
