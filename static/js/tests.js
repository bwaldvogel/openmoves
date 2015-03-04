QUnit.test( "celcius tests", function( assert ) {
	assert.ok( celcius(273.15) == 0, "Passed!" );
	assert.ok( celcius(340.1) == 340.1 - 273.15, "Passed!" );
});

QUnit.test( "x/min tests", function( assert ) {
	assert.ok( per_min(27) == 27 * 60, "Passed!" );
});

QUnit.test( "bpm tests", function( assert ) {
	assert.ok( bpm(23) == 23 * 60, "Passed!" );
});

QUnit.test( "km/h tests", function( assert ) {
	assert.ok( kmh(4.3) == 4.3 * 3.6, "Passed!" );
});

QUnit.test( "pruneNulls tests", function( assert ) {
	assert.deepEqual( pruneNulls([]), [], "Empty" );

	assert.deepEqual( pruneNulls([
							['x', null],
							['x', null]
							]),
						[], "Only nulls" );

	assert.deepEqual( pruneNulls([
							['x', 1],
							['y', 2]]),
						[
							['x', 1],
							['y', 2]
						], "Simple array" );

	assert.deepEqual( pruneNulls([
							['x', 1],
							['a', null],
							['b', null],
							['y', 2]
						]),
						[
							['x', 1],
							['y', 2]
						], "Mixed array" );

	assert.deepEqual( pruneNulls([
							['a', null],
							['x', 1]
						]),
						[
							['x', 1]
						], "Null at beginning" );

	assert.deepEqual( pruneNulls([
							['x', 1],
							['a', null]
						]),
						[
							['x', 1]
						], "Null at end" );
});

QUnit.test( "pruneLowDeltas tests", function( assert ) {
	assert.deepEqual( pruneLowDeltas([], 0.0), [], "Empty with zero delta" );
	assert.deepEqual( pruneLowDeltas([], 1.0), [], "Empty with positive delta" );
	assert.deepEqual( pruneLowDeltas([['x', null]], 1.0), [['x', null]], "Only null element" );
	assert.deepEqual( pruneLowDeltas([['x', 7]], 1.0), [['x', 7]], "Single element" );

	assert.deepEqual( pruneLowDeltas([
							['x', 1],
							['x', 2],
							['x', 3]
						], 1.0),
						[
							['x', 1],
							['x', 2],
							['x', 3]
						],
						"Array without nulls; without low deltas" );

	assert.deepEqual( pruneLowDeltas([
							['x', 1],
							['x', 2],
							['x', null],
							['x', 3]
						], 1.0),
						[
							['x', 1],
							['x', 2],
							['x', null],
							['x', 3]
						],
						"Array with nulls; without low deltas " );

	assert.deepEqual( pruneLowDeltas([
							['x', 1],
							['x', 2],
							['x', null],
							['x', 2.5],
							['x', 3],
							['x', 3.3],
							['x', null],
							['x', 4]
						], 1.0),
						[
							['x', 1],
							['x', 2],
							['x', null],
							['x', 2.5],
							['x', 3.3],
							['x', null],
							['x', 4]
						],
						"Array with nulls; with low deltas " );

	assert.deepEqual( pruneLowDeltas([
							['x', 1.0],
							['x', 1.5],
							['x', 2.3],
							['x', 2.4],
							['x', 2.5]
						], 1.0),
						[
							['x', 1.0],
							['x', 2.3],
							['x', 2.5]
						],
						"Array without nulls; many low deltas " );

	assert.deepEqual( pruneLowDeltas([
							['x', 1.0],
							['x', 1.1],
							['x', 1.2],
							['x', 1.3],
							['x', 1.4],
							['x', 1.5]
						], 1.0),
						[
							['x', 1.0],
							['x', 1.5]
						],
						"Array without nulls; only low deltas " );

	assert.deepEqual( pruneLowDeltas([
							['x', null],
							['x', 1.0],
							['x', 1.1],
							['x', 1.2],
							['x', null],
							['x', 1.3],
							['x', 1.4],
							['x', 1.5]
						], 1.0),
						[
							['x', null],
							['x', 1.0],
							['x', 1.2],
							['x', null],
							['x', 1.3],
							['x', 1.5]
						],
						"Array with nulls; only low deltas " );
});

QUnit.test( "moveMean tests", function( assert ) {
	assert.deepEqual( moveMean([], 3), [], "Empty" );
});
