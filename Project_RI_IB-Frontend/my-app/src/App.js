import logo from './logo.svg';
import './App.css';
import Title from './components/Title';
import SearchAndTableComponent from './components/searchAndTable';


function App() {
  return (
    <div className="App">
      <header className="App-header">
        <Title/>
        <SearchAndTableComponent/>  
      </header>
      <div>

      </div>
    </div>
  );
}

export default App;
