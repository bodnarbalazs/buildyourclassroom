---
area: general
type: reference
---
# Cs2Ts

A custom .NET global tool that generates TypeScript type definitions from C# domain models. Keeps the frontend's generated types in sync with the backend.

---

## Installation

Install from nuget (Balazs.Cs2Ts)

```powershell
dotnet tool install --global Balazs.Cs2Ts
```

### Updating

```powershell
dotnet tool update --global Balazs.Cs2Ts
```
Note: While the package name had to be prefixed for nuget, the tool is still called cs2ts.

---

## Usage

Run from the Domain project directory:

```powershell
cd C:\Users\User\Desktop\LC\src\backend\LC.Domain
cs2ts "..\..\frontend\src\generated"
```

This generates TypeScript types into `src/frontend/src/generated/`.

---

## Related

- [Architecture Overview](../understand/architecture.md) — How frontend and backend connect
