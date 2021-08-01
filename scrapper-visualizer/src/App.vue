<template>
  <div id="app">
    <p>
      Source: <a href="https://www.hak.hr/info/stanje-na-cestama/?lang=en#border-crossings">hak.hr</a>
    </p>
    <highcharts :options="chartToCroatiaOptions" :callback="afterChartToCreate"></highcharts>
    <highcharts :options="chartFromCroatiaOptions" :callback="afterChartFromCreate"></highcharts>
  </div>
</template>

<script>
import { Chart } from 'highcharts-vue';

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
}

export default {
  name: 'App',
  components: {
    highcharts: Chart
  },
  data() {
    return {
      chartTo: null,
      chartFrom: null,
      ignoredCrossings: [
        'Jasenovac', 'Duboševica', 'Goričan II', 'Bajakovo', 'Pasjak',
        'Stara Gradiška', 'Županja', 'Slavonski Brod', 'Maljevac', 'Slavonski Šamac',
        'Tovarnik', 'Kamensko', 'Vinjani Gornji', 'Dvor', 'Goričan', 'Aržano',
        'Zaton Doli',
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
    };
  },
  async created() {
    const url = process.env.NODE_ENV === 'development' ? '/history.sample.json' : '/history.json';
    const response = await fetch(url);
    history = await response.json();
    this.refreshCharts();
  },
  methods: {
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
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
