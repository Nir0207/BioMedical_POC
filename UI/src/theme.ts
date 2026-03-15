import { createTheme } from "@mui/material/styles";

export const biomedicalTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1d4d5b"
    },
    secondary: {
      main: "#b3523b"
    },
    background: {
      default: "#f6f1e8",
      paper: "#fffaf2"
    },
    text: {
      primary: "#11212d",
      secondary: "#41525d"
    }
  },
  shape: {
    borderRadius: 18
  },
  typography: {
    fontFamily: '"IBM Plex Sans", "Segoe UI", sans-serif',
    h3: {
      fontWeight: 700,
      letterSpacing: "-0.04em"
    },
    h4: {
      fontWeight: 700,
      letterSpacing: "-0.03em"
    },
    h5: {
      fontWeight: 700
    }
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none"
        }
      }
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true
      },
      styleOverrides: {
        root: {
          borderRadius: 999,
          textTransform: "none",
          fontWeight: 700
        }
      }
    }
  }
});
