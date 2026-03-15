import forms from "@tailwindcss/forms";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f4efe6",
        ink: "#11212d",
        sea: "#1d4d5b",
        algae: "#2f6b5f",
        ember: "#b3523b",
        sand: "#dcc8a7"
      },
      boxShadow: {
        dashboard: "0 24px 80px rgba(17, 33, 45, 0.14)"
      },
      backgroundImage: {
        "mesh-warm":
          "radial-gradient(circle at 0% 0%, rgba(179,82,59,0.16), transparent 28%), radial-gradient(circle at 100% 15%, rgba(29,77,91,0.18), transparent 32%), linear-gradient(180deg, #f6f1e8 0%, #efe5d4 100%)"
      }
    }
  },
  plugins: [forms]
};
