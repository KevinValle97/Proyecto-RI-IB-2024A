// Función que envía una consulta al servidor y establece los resultados en el estado del componente que la llamó.
const sendQuery = (query, setResults) => {
    console.log("queryservic", query);
    fetch('http://localhost:5000/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    })
    .then(response => response.json())
    .then(data => {
        const results = data.result.map((item, index) => ({
            title: item.title,
            content: item.content,
        }));
        setResults(results); // Se establecen los resultados en el estado del componente que llamó a esta función.
    })
    .catch(error => console.error('Error:', error));
};

export default sendQuery;