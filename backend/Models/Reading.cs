namespace Backend.Models;

public class Reading
{
    public int Id { get; set; }
    public int AssetId { get; set; }
    public DateTimeOffset Timestamp { get; set; }
    public double Temperature { get; set; } // Celsius
    public double Pressure { get; set; }    // PSI

    public Asset Asset { get; set; } = null!;
}
