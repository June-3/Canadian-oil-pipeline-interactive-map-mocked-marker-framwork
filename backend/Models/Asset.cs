namespace Backend.Models;

public class Asset
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Type { get; set; } = ""; // "sensor" or "valve"
    public double Longitude { get; set; }
    public double Latitude { get; set; }
    public string Status { get; set; } = "normal"; // normal / warning / alarm
    public DateTime UpdatedAt { get; set; }

    public List<Reading> Readings { get; set; } = [];
}
