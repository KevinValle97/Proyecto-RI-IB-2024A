import React, { useState } from 'react';
import PropTypes from 'prop-types';
import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import sendQuery from '../services/sendQuery';

// Componente que contiene un campo de texto y un botón para realizar una búsqueda en el servidor.
const SearchAndTableComponent = () => {
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState(false);
  const [results, setResults] = useState([]);

  const handleInputChange = (event) => {
    const { value } = event.target;
    if (/^[a-zA-Z\s]*$/.test(value)) {
      setInputText(value);
      setError(false);
    } else {
      setError(true);
    }
  };

  const handleOnClick = () => {
    if (!error) {
      sendQuery(inputText, setResults);
    }
  };

  const rows = results.map(result => createData(result.title, result.content));

  return (
    <div>
      <div>
        <input
          type="text"
          value={inputText}
          name="query"
          onChange={handleInputChange}
          placeholder="Enter text"
          style={{ width: '300px', padding: '10px', fontSize: '16px' }}
        />
        <button
          onClick={handleOnClick}
          disabled={error}
          style={{ marginLeft: '10px', padding: '10px 20px', fontSize: '16px' }}
        >
          Search
        </button>
        {error && (
          <Typography color="red">
            You cannot write numbers or special characters
          </Typography>
        )}
      </div>
      <TableContainer component={Paper}>
        <Table aria-label="collapsible table">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell>Search Result</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <Row key={index} row={row} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
};

// Función que crea un objeto con los datos de un resultado.
function createData(titulo, summary) {
  return {
    titulo,
    summary,
  };
}

// Componente que muestra una fila de la tabla.
function Row(props) {
  const { row } = props;
  const [open, setOpen] = React.useState(false);

  return (
    <React.Fragment>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          {row.titulo}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={2}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1 }}>
              <Typography variant="body1" gutterBottom component="div">
                {row.summary}
              </Typography>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}

// Se establecen los tipos de las propiedades del componente Row.
Row.propTypes = {
  row: PropTypes.shape({
    titulo: PropTypes.string.isRequired,
    summary: PropTypes.string.isRequired,
  }).isRequired,
};

export default SearchAndTableComponent;