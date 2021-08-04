<template>
  <div id="app" class="container">
    <p>
      Source: <a href="https://www.hak.hr/info/stanje-na-cestama/?lang=en#border-crossings">hak.hr</a>
    </p>
    <div>
      <label for="select-day">Show Stats for Day of Week:</label>
      <select id="select-day" v-model="selectedDay" @change="displayDailyGraphs">
        <option v-for="[dayOfWeek, dayName] of days" :key="dayOfWeek" :value="dayOfWeek">{{ dayName }}</option>
      </select>
    </div>
    <div v-show="selectedDay === 0 || selectedDay">
      <button @click.prevent="hideAll('dayChartTo')">Hide All</button>
      <button @click.prevent="showAll('dayChartTo')">Show All</button>
      <highcharts :options="dayChartToCroatiaOptions" :callback="afterDayChartToCreate" />
      <hr>
      <button @click.prevent="hideAll('dayChartFrom')">Hide All</button>
      <button @click.prevent="showAll('dayChartFrom')">Show All</button>
      <highcharts :options="dayChartFromCroatiaOptions" :callback="afterDayChartFromCreate" />
    </div>
    <hr>
    <h2>Historical Data</h2>
    <div>
      <button @click.prevent="hideAll('chartTo')">Hide All</button>
      <button @click.prevent="showAll('chartTo')">Show All</button>
    </div>
    <highcharts :options="chartToCroatiaOptions" :callback="afterChartToCreate"></highcharts>
    <hr>
    <div>
      <button @click.prevent="hideAll('chartFrom')">Hide All</button>
      <button @click.prevent="showAll('chartFrom')">Show All</button>
    </div>
    <highcharts :options="chartFromCroatiaOptions" :callback="afterChartFromCreate"></highcharts>
  </div>
</template>

<script>
import { Chart } from 'highcharts-vue';
import { fromUnixTime, getDay, getHours } from 'date-fns';

let history = {};
const crossingCoordinates = {};
const convertDEGToDMS = (deg, isLat) => {
  const absolute = Math.abs(deg);
  const degrees = Math.floor(absolute);
  const minutesNotTruncated = (absolute - degrees) * 60;
  const minutes = Math.floor(minutesNotTruncated);
  const seconds = ((minutesNotTruncated - minutes) * 60).toFixed(2);

  let direction;
  if (isLat) {
    direction = deg >= 0 ? "N" : "S";
  } else {
    direction = deg >= 0 ? "E" : "W";
  }

  return `${degrees}°${minutes}'${seconds}"${direction}`;
}

const chartOptions = {
  title: {
    text: 'Entering Croatia',
  },
  xAxis: {
    type: 'datetime',
  },
  yAxis: {
    title: {
      text: 'Wait time (min)',
    },
  },
  legend: {
    labelFormatter() {
      if (!crossingCoordinates[this.name]) {
        return this.name;
      }
      const point = crossingCoordinates[this.name];
      let dmsLat = convertDEGToDMS(point.y, true);
      let dmsLng = convertDEGToDMS(point.x, false);
      let url = `https://www.google.com/maps/place/${dmsLat}+${dmsLng}/@${point.y},${point.x},17z/`
      // NOTE: href is missing " intentionally, due to dms formatting and highcharts eating up quotes
      return `${this.name} (<a href=${url} target="_blank" style="text-decoration: underline;">Map</a>)`;
    },
  },
  tooltip: {
    pointFormatter() {
      const hours = Math.floor(this.y / 60);
      const minutes = this.y - hours * 60;
      let formattedTime = `${hours ? `${hours}h ` : ''}`;
      if (hours && minutes) {
        formattedTime += `${minutes}min`
      } else if (!hours) {
        formattedTime += `${minutes}`
      }
      return `<span style="color: ${this.series.color};">\u25CF</span> ${this.series.name}: <b> ${formattedTime}</b>`
    }
  },
  plotOptions: {
    series: {
      label: {
        connectorAllowed: false
      },
    }
  },
};

const dayChartOptions = {
  xAxis: {
    title: {
      text: 'Hour of Day'
    }
  },
  yAxis: {
    title: {
      text: 'Avg Wait Time (min)',
    },
  },
  plotOptions: {
    series: {
      label: {
        connectorAllowed: false
      },
    }
  },
};

export default {
  name: 'App',
  components: {
    highcharts: Chart
  },
  data() {
    return {
      seriesByDayAndHour: null,
      dayChartTo: null,
      dayChartFrom: null,
      chartTo: null,
      chartFrom: null,
      days: [
        [1, 'Monday'],
        [2, 'Tuesday'],
        [3, 'Wednesday'],
        [4, 'Thursday'],
        [5, 'Friday'],
        [6, 'Saturday'],
        [0, 'Sunday'],
      ],
      selectedDay: '',
      ignoredCrossings: [
        'Jasenovac', 'Duboševica', 'Goričan II', 'Bajakovo', 'Pasjak',
        'Stara Gradiška', 'Županja', 'Slavonski Brod', 'Maljevac', 'Slavonski Šamac',
        'Tovarnik', 'Kamensko', 'Vinjani Gornji', 'Dvor', 'Goričan', 'Aržano',
        'Zaton Doli', 'Ličko Petrovo Selo', 'Metković', 'Nova Sela',
          'Vinjani Donji', 'Hrvatska Kostajnica',
      ],
      chartToCroatiaOptions: {
        ...chartOptions,
        title: {
          text: 'Entering Croatia',
        }
      },
      chartFromCroatiaOptions: {
        ...chartOptions,
        title: {
          text: 'Leaving Croatia',
        }
      },
      dayChartToCroatiaOptions: {
        ...dayChartOptions,
        title: {
          text: 'Entering Croatia on Selected Day',
        }
      },
      dayChartFromCroatiaOptions: {
        ...dayChartOptions,
        title: {
          text: 'Leaving Croatia on Selected Day',
        }
      },
    };
  },
  async created() {
    const url = process.env.NODE_ENV === 'development' ? '/history.sample.json' : '/history.json';
    const response = await fetch(url);
    history = await response.json();
    this.buildStats();
    this.refreshCharts();
  },
  methods: {
    displayDailyGraphs() {
      this.displayDataForDay('from_cro', 'dayChartFrom');
      this.displayDataForDay('to_cro', 'dayChartTo');
    },
    displayDataForDay(direction, targetChart) {
      let key;
      let series = {};
      for (let { name, data } of Object.values(this.seriesByDayAndHour)) {
        let aggregatedData = [];
        for (let i = 0; i < 24; i++) {
          key = `${this.selectedDay}_${i}`;

          let avg;
          if (key in data) {
            avg = data[key][direction].reduce((acc, x) => acc + x, 0) / data[key][direction].length;
          } else {
            avg = 0;
          }

          aggregatedData.push([i, avg]);
        }

        series[name] = {
          name,
          data: aggregatedData,
          avg: aggregatedData.reduce((acc, x) => acc + x[1], 0) / aggregatedData.length,
          max: aggregatedData.reduce((acc, x) => Math.max(acc, x[1]), 0),
        };
        series[name].name = `${name} (avg. ${Math.floor(series[name].avg)}, max. ${series[name].max})`;
      }

      let seriesArray = Object.values(series);
      seriesArray.sort((a, b) => a.avg - b.avg);
      this[targetChart].update({ series: seriesArray }, true, true)
    },
    buildStats() {
      let series = {};

      for (let [time, crossings] of Object.entries(history)) {
        if (!time || !crossings) {
          continue;
        }

        for (let data of crossings) {
          let crossing = data['crossing']?.trim();
          if (!crossing || this.ignoredCrossings.includes(crossing)) {
            continue;
          }

          if (!(crossing in series)) {
            series[crossing] = {
              name: crossing,
              data: {},
            }
          }

          let date = fromUnixTime(parseInt(time));
          let dayOfWeek = getDay(date);
          let hourOfDay = getHours(date);

          let key = `${dayOfWeek}_${hourOfDay}`;
          if (!(key in series[crossing]['data'])) {
            series[crossing]['data'][key] = {'to_cro': [], 'from_cro': []};
          }
          series[crossing]['data'][key]['to_cro'].push(this.getMinutesFromDescription(data['to_cro']));
          series[crossing]['data'][key]['from_cro'].push(this.getMinutesFromDescription(data['from_cro']));
        }
      }
      this.seriesByDayAndHour = series;
    },
    refreshCharts() {
      if (this.chartFrom && this.chartTo) {
        this.chartTo.update({
          series: this.getChartData('to_cro')
        }, true, true);
        this.chartFrom.update({
          series: this.getChartData('from_cro')
        }, true, true);
      }
    },
    getChartData(borderCrossingDirection) {
      let series = {};

      for (let [time, crossings] of Object.entries(history)) {
        if (!time || !crossings) {
          continue;
        }

        for (let data of crossings) {
          let crossing = data['crossing']?.trim();
          if (!crossing || this.ignoredCrossings.includes(crossing.trim())) {
            continue;
          }

          if (data['coordinate_x'] && data['coordinate_y']) {
            crossingCoordinates[crossing] = {
              x: data['coordinate_x'],
              y: data['coordinate_y'],
            };
          }

          if (!(crossing in series)) {
            series[crossing] = {
              name: crossing,
              data: [],
            }
          }

          let minutes = this.getMinutesFromDescription(data[borderCrossingDirection]);
          let timestamp = (7200 + parseInt(time)) * 1000; // adding 7200 as a timezone hack...
          series[crossing]['data'].push([timestamp, minutes]);
        }
      }

      return Object.values(series);
    },
    getMinutesFromDescription(time_desc) {
      time_desc = time_desc.trim();
      if (time_desc === 'do 30 min.') {
        return 30;
      }

      let regexp = /([0-9]*)\s*h\s*([0-9]*)?/g;
      let results = [...time_desc.matchAll(regexp)];

      if (results.length > 0) {
        return results[0][1] * 60 + (results[0][2] ? parseInt(results[0][2]) : 0);
      }

      if (time_desc !== '-') {
        console.warning('Strange empty detected', time_desc);
      }

      return 0;
    },
    hideAll(chart) {
      for (let series of this[chart].series) {
        series.hide();
      }
    },
    showAll(chart) {
      for (let series of this[chart].series) {
        series.show();
      }
    },
    afterChartToCreate(chart) {
      this.chartTo = chart;
      this.chartTo.update({
        series: this.getChartData('to_cro')
      }, true, true);
    },
    afterChartFromCreate(chart) {
      this.chartFrom = chart;
      this.chartFrom.update({
        series: this.getChartData('from_cro')
      }, true, true);
    },
    afterDayChartToCreate(chart) {
      this.dayChartTo = chart;
    },
    afterDayChartFromCreate(chart) {
      this.dayChartFrom = chart;
    },
  }
}
</script>

<style>
#app {
  margin: 30px;
}
button {
  margin-right: 0.5rem;
}
</style>
