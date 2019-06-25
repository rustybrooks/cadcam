import PropTypes from 'prop-types';
import React from 'react';

const localStyles = {
  wrapper: {
    backfaceVisibility: 'hidden',
    position: 'absolute',
    top: 0,
    left: 0,
    zIndex: 2,
    transform: 'rotateY(0deg)',
    width: '100%',
  },
  inputWrapper: {
    display: 'flex',
    flexFlow: 'row wrap',
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonsWrapper: {
    display: 'flex',
    flexFlow: 'row wrap',
    justifyContent: 'center',
    alignItems: 'center',
  },
  input: {
    width: 344,
    height: 40,
    margin: '15px 0',
  },
  recoverPasswordWrapper: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row wrap',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recoverPassword: {
    textAlign: 'center',
    cursor: 'pointer',
    margin: '20px 0',
    padding: 15,
  },
  button: {
    margin: '0 15px',
    padding: 15,
  },
};

const Login = ({
  handleShowSignup,
  handleShowRecover,
  handleLogin,
  handleChange,
  username,
  password,
}) => (
  <section id="login-form" style={localStyles.wrapper}>
    <div id="fields" style={localStyles.inputWrapper}>
      <input
        style={localStyles.input}
        type="text"
        id="username"
        name="username"
        placeholder='Username'
        onChange={e => handleChange(e.target.name, e.target.value)}
        value={username}
      />
      <input
        style={localStyles.input}
        type="password"
        id="password"
        name="password"
        placeholder='Password'
        onChange={e => handleChange(e.target.name, e.target.value)}
        value={password}
      />
    </div>
    <div style={localStyles.buttonsWrapper}>
      <div
        style={localStyles.recoverPasswordWrapper}
      >
        {/*<button*/}
          {/*id="recorver-password"*/}
          {/*type="button"*/}
          {/*style={localStyles.recoverPassword}*/}
          {/*onClick={() => {*/}
            {/*handleShowRecover('isRecoveringPassword', true);*/}
          {/*}}*/}
        {/*>*/}
          {/*Recover*/}
        {/*</button>*/}
      </div>
      <button
        id="signup-button"
        type="button"
        style={localStyles.button}
        onClick={() => {
          handleShowSignup('isLogin', false);
        }}
      >
        Signup
      </button>
      <input
        id="submit-login"
        name="submit-login"
        value='Login'
        type="submit"
        style={localStyles.button}
        onClick={handleLogin}
      />
    </div>
  </section>
);

Login.propTypes = {
  handleShowSignup: PropTypes.func.isRequired,
  handleShowRecover: PropTypes.func.isRequired,
  handleLogin: PropTypes.func.isRequired,
  handleChange: PropTypes.func.isRequired,
  username: PropTypes.string.isRequired,
  password: PropTypes.string.isRequired,
};


export default Login;
