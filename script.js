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

class Queue {
  constructor(len) {
    this.q = Array(len + 1);
    this.head = 0;
    this.tail = 0;
    this.len = len + 1;
  }
  get front() {
    return this.q[this.head];
  }
  get back() {
    if (this.tail) return this.q[this.tail - 1];
    else return this.q[this.len - 1];
  }
  push(v) {
    this.q[this.tail] = v;
    this.tail++;
    if (this.tail >= this.len) this.tail = 0;
  }
  pop() {
    this.head++;
    if (this.head >= this.len) this.head = 0;
  }
  get size() {
    if (this.tail >= this.head) return this.tail - this.head;
    else return this.tail - this.head + this.len;
  }
}

var lines;
var stations = new Set();
var station2line = new Map();

function load_json() {
  var url = "metro.json";
  var request = new XMLHttpRequest();
  request.open("get", url);
  request.send(null);
  request.onload = function () {
    if (request.status == 200) {
      lines = JSON.parse(request.responseText);
    }
    lines["成都"]["地铁1号线"]["stations"]["阿蒙森—斯科特"] = {};
    for (var city in lines) {
      for (var line in lines[city]) {
        for (var station in lines[city][line]["stations"]) {
          stations.add(station);
          if (station in station2line) {
            station2line[station].push([city, line]);
          } else {
            station2line[station] = [[city, line]];
          }
        }
      }
    }
    var options="";
    for (var station of stations)
      options+='<option value="'+station+'" />';
    document.getElementById("stations").innerHTML=options;
  };
}

load_json();

function getpath(beg, end) {
  if (!(stations.has(beg) && stations.has(end))) return [];
  var N = stations.size;
  var dis = new Map();
  var last_line = new Map();
  var last_station = new Map();
  var q = new Queue(N);
  dis[beg] = 0;
  q.push(beg);
  while (q.size) {
    var t = q.front;
    q.pop();
    if (t == end) break;
    for (var i in station2line[t]) {
      var line = station2line[t][i];
      for (var station in lines[line[0]][line[1]]["stations"]) {
        if (dis[station] == undefined) {
          dis[station] = dis[t] + 1;
          last_line[station] = line;
          last_station[station] = t;
          q.push(station);
        }
      }
    }
  }
  if (dis[end] == undefined) return [];
  var path = [];
  var u = end;
  while (u != beg) {
    path.push({
      start: last_station[u] + "站",
      end: u + "站",
      line: last_line[u][0] + last_line[u][1],
      color: "#" + lines[last_line[u][0]][last_line[u][1]]["color"],
    });
    u = last_station[u];
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
