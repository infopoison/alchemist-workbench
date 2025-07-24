import chartData from './test_chart.json';

function App() {
  // Extract the original SVG string from the imported JSON data
  const originalSvgChart = chartData.chart;

  // This new line makes the SVG a fixed size by replacing its opening tag.
  const responsiveSvgChart = originalSvgChart.replace('<svg ', '<svg width="1400" height="1400" ');

  return (
    <main className="flex justify-center items-center h-screen bg-gray-100 p-4">
      <div
        className="w-full bg-white rounded-lg shadow-lg overflow-hidden"
        // Use the new, smaller SVG string here
        dangerouslySetInnerHTML={{ __html: responsiveSvgChart }}
      />
    </main>
  );
}

export default App;