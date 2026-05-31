using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Backend.Data;

namespace Backend.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AssetsController : ControllerBase
{
    private readonly AppDbContext _db;

    public AssetsController(AppDbContext db)
    {
        _db = db;
    }

    /// <summary>GET /api/assets — all assets with latest reading snapshot.</summary>
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var assets = await _db.Assets
            .OrderBy(a => a.Id)
            .Select(a => new
            {
                a.Id,
                a.Name,
                a.Type,
                a.Longitude,
                a.Latitude,
                a.Status,
                a.UpdatedAt,
                LatestReading = a.Readings
                    .OrderByDescending(r => r.Timestamp)
                    .Select(r => new { r.Temperature, r.Pressure, r.Timestamp })
                    .FirstOrDefault()
            })
            .ToListAsync();

        return Ok(assets);
    }

    /// <summary>GET /api/assets/{id}/readings — latest N readings for one asset.</summary>
    [HttpGet("{id:int}/readings")]
    public async Task<IActionResult> GetReadings(int id, [FromQuery] int count = 1)
    {
        var asset = await _db.Assets.FindAsync(id);
        if (asset == null)
            return NotFound();

        var readings = await _db.Readings
            .Where(r => r.AssetId == id)
            .OrderByDescending(r => r.Timestamp)
            .Take(count)
            .Select(r => new { r.Temperature, r.Pressure, r.Timestamp })
            .ToListAsync();

        return Ok(readings);
    }

    /// <summary>GET /api/assets/{id}/history — historical readings for charting.</summary>
    [HttpGet("{id:int}/history")]
    public async Task<IActionResult> GetHistory(int id, [FromQuery] int limit = 50)
    {
        var asset = await _db.Assets.FindAsync(id);
        if (asset == null)
            return NotFound();

        var history = await _db.Readings
            .Where(r => r.AssetId == id)
            .OrderByDescending(r => r.Timestamp)
            .Take(limit)
            .Select(r => new { r.Temperature, r.Pressure, r.Timestamp })
            .ToListAsync();

        return Ok(history.OrderBy(r => r.Timestamp));
    }
}
