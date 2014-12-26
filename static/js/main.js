function mapData(array, unit) {
    return array.map(function(element) {
        var key = element[0];
        var data = element[1];
        if (data != null) {
            data = unit(data);
        }
        return [key, data];
    });
}

function celcius(val) {
    return val - 273.15;
}

function bpm(val) {
    return val * 60;
}

function kmh(val) {
    return val * 3.6;
}

function pruneNulls(data) {
    var ret = [];
    var before = null
    for (var i=0; i < data.length; i++) {
        if (data[i][1] != null) {
            ret.push(data[i]);
        }
    }
    return ret;
}

function pruneLowDeltas(data, minDelta) {
    if (minDelta == 0.0) {
        return data;
    }
    var ret = [];
    var before = null;
    for (var i=0; i < data.length; i++) {
        if (data[i][1] == null) {
            if (i > 0 && data[i-1] != before) {
                ret.push(data[i-1]);
            }
            ret.push(data[i]);
            before = data[i];
        } else if (before == null || Math.abs(data[i][1] - before[1]) >= minDelta) {
            ret.push(data[i]);
            before = data[i];
        }
    }
    if (ret.length == 1) {
        ret.push(data[data.length - 1]);
    }
    return ret;
}

function moveMean(data, n) {
    var meanData = [];
    var n_2 = Math.floor(n/2);
    for (var i = 0; i < data.length; i++)
    {
        if (data[i][1] == null) {
            meanData.push(data);
        } else {
            var num = 0;
            var mean = 0.0;
            for (var x=0; x<=n_2; x++) {
                if (i+x >= 0 && i+x < data.length) {
                    if (data[i+x][1] == null) {
                        break;
                    }
                    mean += data[i+x][1];
                    num++;
                }
            }
            for (var x=0; x<=n_2; x++) {
                if (i-x >= 0 && i-x < data.length) {
                    if (data[i-x][1] == null) {
                        break;
                    }
                    mean += data[i-x][1];
                    num++;
                }
            }
            meanData.push([data[i][0], mean / num]);
        }
    }
    return meanData;
}

function calculateSpeed(data, distanceInterval, unit) {
    var ret = [];
    var before = null;
    var current = null;
    for (var i=0; i < data.length; i++) {
        if (data[i][1] == null) {
            if (before != null && current != null) {
                var seconds = (current[0] - before[0]) / 1000.0;
                var speed = delta / seconds;
                ret.push([data[i][0], speed]);
            }
            before = null;
            current = null;
            ret.push(data[i]);
            continue;
        }
        if (before != null) {
            var delta = data[i][1] - before[1];
            if (delta >= distanceInterval || i == data.length - 1) {
                var seconds = (data[i][0] - before[0]) / 1000.0;
                var speed = delta / seconds;
                if (ret.length == 0) {
                    ret.push([data[0][0], speed]);
                } else {
                    ret.push([data[i][0], speed]);
                }
                before = data[i];
                current = null;
            } else {
                current = data[i];
            }
        } else {
            before = data[i];
        }
    }
    if (before != null && before != data[data.length - 1]) {
        ret.push(before);
    }
    return mapData(ret, unit);
}
